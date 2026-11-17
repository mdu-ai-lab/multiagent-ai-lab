# The HTTP API of the platform under /v1, served by FastAPI. Experimental until the API is
# frozen: paths and fields may still change. Start it with: make api
# The functions live in service.py. This file only turns HTTP into calls and back.
# Chats need a login or a guest session while an admin allows guest mode. Every changing
# request needs the token of its session (auth.check_request_origin). The same app serves the
# chat page (ui.py) and its files in /static

import dataclasses
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import date
from importlib.metadata import version
from typing import Annotated, Any, Literal

import anyio
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, format_sse_event
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints

from mrag import admin, auth, db, harness, service, ui
from mrag.harness.context import Turn

# The name of each streamed event
EVENT_NAMES = {harness.Delta: "delta", harness.Done: "done", harness.Error: "error"}
# The status a saved answer gets from the last event of its stream. Without one the stream
# was closed early
ANSWER_STATUS = {harness.Done: "done", harness.Error: "failed"}

SAME_SITE_ONLY = [Depends(auth.check_request_origin)]
LOGGED_IN = [Depends(auth.require_user)]
ADMIN_ONLY = [Depends(auth.require_admin)]
User = Annotated[db.User, Depends(auth.require_user)]
Admin = Annotated[db.User, Depends(auth.require_admin)]
# The language and theme cookies keep the choice on the login page after logging out
YEAR = 365 * 24 * 3600


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    service.start()
    service.open_database()
    yield


app = FastAPI(
    title="multiagent-ai-lab API",
    version=version("multiagent-ai-lab"),
    description="Experimental: paths and fields under /v1 may still change.",
    lifespan=lifespan,
)
app.add_middleware(ui.SecurityHeaders)
app.mount("/static", StaticFiles(directory=ui.STATIC), name="static")
app.include_router(ui.router)


def chat_owner(
    s: auth.DbSession,
    browser: auth.SessionRow,
    user: Annotated[db.User | None, Depends(auth.current_user)],
) -> service.Owner:
    if user is not None:
        return service.Owner(user_id=user.id)
    # A guest chats only while an admin allows guest mode. A session whose user was blocked
    # or deleted is never treated as a guest
    if browser is not None and browser.user_id is None and admin.settings(s)["guest_mode"]:
        return service.Owner(session_id=browser.id)
    raise HTTPException(401, "login_required")


ChatOwner = Annotated[service.Owner, Depends(chat_owner)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=ui.MAX_MESSAGE_LENGTH)
    # Empty starts a new chat. The earlier turns come from the saved chat
    chat_id: uuid.UUID | None = None


class RenameRequest(BaseModel):
    title: Title


class Deleted(BaseModel):
    deleted: int


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)
    remember: bool = False


class SignupRequest(BaseModel):
    name: str = Field(max_length=60)
    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)


class UserInfo(BaseModel):
    name: str
    email: str
    role: str

    @classmethod
    def of(cls, user: db.User) -> "UserInfo":
        return cls(name=user.name, email=user.email, role=user.role)


class NameRequest(BaseModel):
    name: str = Field(max_length=200)


class SettingsRequest(BaseModel):
    theme: Literal["dark", "light", "system"] | None = None
    language: Literal["en", "sv"] | None = None
    enter_sends: bool | None = None
    show_examples: bool | None = None
    sidebar_collapsed: bool | None = None


class PasswordRequest(BaseModel):
    current_password: str = Field(max_length=1024)
    new_password: str = Field(max_length=1024)
    confirm_password: str = Field(max_length=1024)


class DeleteAccountRequest(BaseModel):
    password: str = Field(max_length=1024)


class FeedbackRequest(BaseModel):
    kind: Literal["problem", "idea", "other"]
    message: str = Field(max_length=2000)


class CreateUserRequest(BaseModel):
    name: str = Field(max_length=200)
    email: str = Field(max_length=300)
    password: str = Field(max_length=1024)
    role: Literal["member", "admin"] = "member"


class UpdateUserRequest(BaseModel):
    role: Literal["member", "admin"] | None = None
    blocked: bool | None = None


class FeedbackDoneRequest(BaseModel):
    done: bool


class AdminSettingsRequest(BaseModel):
    guest_mode: bool | None = None
    guest_limit: int | None = None
    signup_open: bool | None = None


@app.get("/v1/health")
def health() -> service.Health:
    return service.health()


@app.get("/v1/version")
def get_version() -> service.VersionInfo:
    return service.version()


@app.post("/v1/auth/login", dependencies=SAME_SITE_ONLY)
def log_in(
    body: LoginRequest,
    request: Request,
    response: Response,
    s: auth.DbSession,
    browser: auth.SessionRow,
) -> UserInfo:
    # A new session replaces this browser's session. Every failed login gives the same answer
    try:
        token, user = auth.log_in(s, body.email, body.password, body.remember, browser)
    except auth.LoginFailed:
        raise HTTPException(401, "login_failed") from None
    s.commit()
    auth.set_session_cookie(response, request, token, body.remember)
    return UserInfo.of(user)


@app.post("/v1/auth/signup", dependencies=SAME_SITE_ONLY)
def sign_up(
    body: SignupRequest,
    request: Request,
    response: Response,
    s: auth.DbSession,
    browser: auth.SessionRow,
) -> UserInfo:
    # Only while an admin allows sign-up. The new account is logged in at once
    if not admin.settings(s)["signup_open"]:
        raise HTTPException(403, "signup_closed")
    try:
        user = auth.create_user(s, body.email, body.name, body.password)
    except auth.AccountError as error:
        raise HTTPException(400, error.code) from None
    if browser is not None:
        s.delete(browser)
    user.last_login_at = db.utcnow()
    token, _ = auth.start_session(s, user)
    s.commit()
    auth.set_session_cookie(response, request, token, remember=False)
    return UserInfo.of(user)


@app.post("/v1/auth/logout", dependencies=SAME_SITE_ONLY, status_code=204)
def log_out(request: Request, s: auth.DbSession, browser: auth.SessionRow) -> Response:
    if browser is not None:
        s.delete(browser)
        s.commit()
    response = Response(status_code=204)
    auth.clear_session_cookie(response, request)
    return response


@app.get("/v1/models", dependencies=LOGGED_IN)
def models() -> service.ProfileModels:
    return service.models()


@app.post(
    "/v1/chat",
    dependencies=SAME_SITE_ONLY,
    responses={200: {"content": {"text/event-stream": {}}, "description": "Server-Sent Events"}},
)
async def chat(
    body: ChatRequest, s: auth.DbSession, owner: ChatOwner, browser: auth.SessionRow
) -> EventSourceResponse:
    # Streams events: chat (its ID and title), delta (a piece of the answer), then done (the
    # answer and the totals) or error (its kind and a short message). The question is saved
    # before the answer starts and the answer when its stream ends.
    # The stream is built here instead of by FastAPI's own event streaming: there a closed
    # connection did not reach this code, so the model kept writing. Here it cancels the
    # stream, which closes the answer at once
    def begin() -> tuple[uuid.UUID, str, list[Turn]]:
        if owner.session_id is not None and browser is not None:
            service.count_guest_message(s, browser)
        started = service.start_turn(s, owner, body.chat_id, body.message)
        s.commit()
        return started

    try:
        chat_id, title, history = await anyio.to_thread.run_sync(begin)
    except service.ChatNotFound:
        raise HTTPException(404, "chat_not_found") from None
    except service.GuestLimitReached:
        raise HTTPException(403, "guest_limit") from None
    events = service.chat(body.message, history)

    async def stream() -> AsyncIterator[bytes]:
        pieces: list[str] = []
        status = "stopped"
        try:
            opened = json.dumps({"chat_id": str(chat_id), "title": title}, ensure_ascii=False)
            yield format_sse_event(event="chat", data_str=opened)
            # Each event is read in a worker thread, so the server stays free meanwhile
            while (event := await anyio.to_thread.run_sync(next, events, None)) is not None:
                if isinstance(event, harness.Delta):
                    pieces.append(event.text)
                status = ANSWER_STATUS.get(type(event), status)
                data = json.dumps(asdict(event), ensure_ascii=False)
                yield format_sse_event(event=EVENT_NAMES[type(event)], data_str=data)
        finally:
            # Closing the events stops the model call. The shield lets the close and the save
            # finish although the stream itself was cancelled
            with anyio.CancelScope(shield=True):
                await anyio.to_thread.run_sync(events.close)
                answer = "".join(pieces)
                await anyio.to_thread.run_sync(service.finish_turn, chat_id, answer, status)

    return EventSourceResponse(stream())


@app.get("/v1/chats")
def list_chats(s: auth.DbSession, owner: ChatOwner) -> list[service.ChatSummary]:
    # Newest first
    return service.list_chats(s, owner)


@app.get("/v1/chats/{chat_id}")
def get_chat(chat_id: uuid.UUID, s: auth.DbSession, owner: ChatOwner) -> service.ChatDetail:
    # Every answer also comes as safe HTML made from its Markdown
    try:
        found = service.get_chat(s, owner, chat_id)
    except service.ChatNotFound:
        raise HTTPException(404, "chat_not_found") from None
    messages = [
        dataclasses.replace(m, html=ui.answer_html(m.content)) if m.role == "assistant" else m
        for m in found.messages
    ]
    return dataclasses.replace(found, messages=messages)


@app.patch("/v1/chats/{chat_id}", dependencies=SAME_SITE_ONLY)
def rename_chat(
    chat_id: uuid.UUID, body: RenameRequest, s: auth.DbSession, owner: ChatOwner
) -> service.ChatSummary:
    try:
        renamed = service.rename_chat(s, owner, chat_id, body.title)
    except service.ChatNotFound:
        raise HTTPException(404, "chat_not_found") from None
    s.commit()
    return renamed


@app.delete("/v1/chats/{chat_id}", dependencies=SAME_SITE_ONLY, status_code=204)
def delete_chat(chat_id: uuid.UUID, s: auth.DbSession, owner: ChatOwner) -> Response:
    try:
        service.delete_chat(s, owner, chat_id)
    except service.ChatNotFound:
        raise HTTPException(404, "chat_not_found") from None
    s.commit()
    return Response(status_code=204)


@app.delete("/v1/chats", dependencies=SAME_SITE_ONLY)
def delete_all_chats(s: auth.DbSession, owner: ChatOwner) -> Deleted:
    deleted = service.delete_all_chats(s, owner)
    s.commit()
    return Deleted(deleted=deleted)


# The account of a logged-in user: the account menu and the settings of the chat page


@app.patch("/v1/me", dependencies=SAME_SITE_ONLY)
def update_name(body: NameRequest, s: auth.DbSession, user: User) -> dict[str, str]:
    try:
        name = service.set_name(user, body.name)
    except auth.AccountError as error:
        raise HTTPException(400, error.code) from None
    s.commit()
    return {"name": name, "initials": ui.initials(name)}


@app.patch("/v1/me/preferences", dependencies=SAME_SITE_ONLY)
def update_settings(
    body: SettingsRequest, request: Request, s: auth.DbSession, user: User
) -> JSONResponse:
    settings = ui.page_settings(request, user)
    settings.update(body.model_dump(exclude_none=True))
    # A new dict, so the database sees the change
    user.settings = dict(settings)
    s.commit()
    response = JSONResponse(settings)
    for name, value in (("lang", settings["language"]), ("theme", settings["theme"])):
        response.set_cookie(name, value, max_age=YEAR, httponly=True, samesite="strict")
    return response


@app.post("/v1/me/password", dependencies=SAME_SITE_ONLY)
def change_password(
    body: PasswordRequest,
    request: Request,
    response: Response,
    s: auth.DbSession,
    user: User,
    browser: auth.SessionRow,
) -> dict[str, bool]:
    # Every other login of the account ends. This browser stays logged in with a new session
    if body.new_password != body.confirm_password:
        raise HTTPException(400, "password_match")
    remember = browser.remember if browser else False
    try:
        token = auth.change_password(s, user, body.current_password, body.new_password, remember)
    except auth.AccountError as error:
        raise HTTPException(400, error.code) from None
    s.commit()
    auth.set_session_cookie(response, request, token, remember)
    return {"changed": True}


@app.get("/v1/me/export")
def export_chats(s: auth.DbSession, user: User) -> JSONResponse:
    filename = f"mdu-ai-lab-chats-{date.today():%Y-%m-%d}.json"
    return JSONResponse(
        service.export_chats(s, user),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/v1/me/delete", dependencies=SAME_SITE_ONLY)
def delete_account(
    body: DeleteAccountRequest, request: Request, s: auth.DbSession, user: User
) -> JSONResponse:
    try:
        service.delete_account(s, user, body.password)
    except auth.AccountError as error:
        raise HTTPException(400, error.code) from None
    s.commit()
    response = JSONResponse({"deleted": True})
    auth.clear_session_cookie(response, request)
    return response


@app.post("/v1/feedback", dependencies=SAME_SITE_ONLY)
def send_feedback(body: FeedbackRequest, s: auth.DbSession, user: User) -> dict[str, Any]:
    try:
        service.add_feedback(s, user, body.kind, body.message)
    except auth.AccountError as error:
        raise HTTPException(400, error.code) from None
    s.commit()
    return {"sent": True}


# The admin panel. Every route needs the admin role, checked on the server


def admin_error(error: auth.AccountError) -> HTTPException:
    return HTTPException(404 if error.code.endswith("not_found") else 400, error.code)


@app.get("/v1/admin/stats", dependencies=ADMIN_ONLY)
def admin_stats(s: auth.DbSession) -> dict[str, int]:
    return admin.stats(s)


@app.get("/v1/admin/users", dependencies=ADMIN_ONLY)
def admin_users(s: auth.DbSession) -> list[dict[str, Any]]:
    return admin.user_list(s)


@app.post("/v1/admin/users", dependencies=SAME_SITE_ONLY)
def admin_create_user(body: CreateUserRequest, s: auth.DbSession, acting: Admin) -> dict[str, int]:
    try:
        user = admin.create_user(s, acting, body.name, body.email, body.password, body.role)
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return {"id": user.id}


@app.patch("/v1/admin/users/{user_id}", dependencies=SAME_SITE_ONLY)
def admin_update_user(
    user_id: int, body: UpdateUserRequest, s: auth.DbSession, acting: Admin
) -> dict[str, bool]:
    try:
        admin.update_user(s, acting, user_id, body.role, body.blocked)
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return {"updated": True}


@app.post("/v1/admin/users/{user_id}/reset-password", dependencies=SAME_SITE_ONLY)
def admin_reset_password(user_id: int, s: auth.DbSession, acting: Admin) -> dict[str, str]:
    try:
        password = admin.reset_password(s, acting, user_id)
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return {"password": password}


@app.delete("/v1/admin/users/{user_id}", dependencies=SAME_SITE_ONLY)
def admin_delete_user(user_id: int, s: auth.DbSession, acting: Admin) -> dict[str, bool]:
    try:
        admin.delete_user(s, acting, user_id)
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return {"deleted": True}


@app.get("/v1/admin/feedback", dependencies=ADMIN_ONLY)
def admin_feedback(s: auth.DbSession) -> list[dict[str, Any]]:
    return admin.feedback_list(s)


@app.patch("/v1/admin/feedback/{feedback_id}", dependencies=SAME_SITE_ONLY)
def admin_update_feedback(
    feedback_id: int, body: FeedbackDoneRequest, s: auth.DbSession, acting: Admin
) -> dict[str, bool]:
    try:
        admin.set_feedback_done(s, acting, feedback_id, body.done)
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return {"done": body.done}


@app.get("/v1/admin/settings", dependencies=ADMIN_ONLY)
def admin_get_settings(s: auth.DbSession) -> dict[str, Any]:
    return admin.settings(s)


@app.patch("/v1/admin/settings", dependencies=SAME_SITE_ONLY)
def admin_update_settings(
    body: AdminSettingsRequest, s: auth.DbSession, acting: Admin
) -> dict[str, Any]:
    try:
        saved = admin.update_settings(s, acting, body.model_dump(exclude_none=True))
    except auth.AccountError as error:
        raise admin_error(error) from None
    s.commit()
    return saved


@app.get("/v1/admin/log", dependencies=ADMIN_ONLY)
def admin_log(s: auth.DbSession) -> list[dict[str, Any]]:
    # The newest admin actions first
    return admin.activity(s)
