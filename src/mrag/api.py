# The HTTP API of the platform under /v1, served by FastAPI. Experimental until the API is
# frozen: paths and fields may still change. Start it with: make api
# The functions live in service.py. This file only turns HTTP into calls and back.
# Chats need a login or a guest session while an admin allows guest mode. Every changing
# request needs the token of its session (auth.check_request_origin)

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from importlib.metadata import version
from typing import Annotated

import anyio
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.sse import EventSourceResponse, format_sse_event
from pydantic import BaseModel, Field, StringConstraints

from mrag import admin, auth, db, harness, service
from mrag.harness.context import Turn

# The name of each streamed event
EVENT_NAMES = {harness.Delta: "delta", harness.Done: "done", harness.Error: "error"}
# The status a saved answer gets from the last event of its stream. Without one the stream
# was closed early
ANSWER_STATUS = {harness.Done: "done", harness.Error: "failed"}

SAME_SITE_ONLY = [Depends(auth.check_request_origin)]
LOGGED_IN = [Depends(auth.require_user)]


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
    message: str = Field(min_length=1)
    # Empty starts a new chat. The earlier turns come from the saved chat
    chat_id: uuid.UUID | None = None


class RenameRequest(BaseModel):
    title: Title


class Deleted(BaseModel):
    deleted: int


@app.get("/v1/health")
def health() -> service.Health:
    return service.health()


@app.get("/v1/version")
def get_version() -> service.VersionInfo:
    return service.version()


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
    try:
        return service.get_chat(s, owner, chat_id)
    except service.ChatNotFound:
        raise HTTPException(404, "chat_not_found") from None


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
