# Core functions of the platform, shared by the API, the chat page, the demo and the tests.
# Questions go to the agent harness through harness.run() with the route table below.
# service.py never creates a model client or calls the search or a tool itself.
# Saved chats: every turn is saved in the chat tables, which harness/memory.py reads back

import logging
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from typing import Any

from sqlalchemy import ColumnElement, delete, func, select
from sqlalchemy.orm import Session

from mrag import admin, auth, db, harness, tracing
from mrag.config import get_settings
from mrag.harness import memory
from mrag.harness.context import Turn
from mrag.harness.loop import Events
from mrag.llm_client import load_models

log = logging.getLogger(__name__)


def chat_route(handle: harness.Harness) -> Iterator[str]:
    # Plain chat: the main model answers with the system prompt and the earlier turns
    return handle.answer()


# The routes a request can take. A router picks among them when there are more
ROUTES: dict[str, harness.Route] = {"chat": chat_route}


@dataclass(frozen=True)
class Health:
    status: str


@dataclass(frozen=True)
class VersionInfo:
    package: str
    profile: str
    git_commit: str
    git_dirty: bool
    pipeline_version: str


@dataclass(frozen=True)
class ModelInfo:
    role: str
    name: str
    source: str
    revision: str | None


@dataclass(frozen=True)
class ProfileModels:
    profile: str
    models: list[ModelInfo]


def start() -> None:
    # Called once when the API starts. Traces go to MLflow only while its server answers,
    # because the MLflow client retries for minutes when the server is down
    settings = get_settings()
    if tracing.setup(settings) and not tracing.server_reachable():
        tracing.setup(settings, trace=False)
        log.warning(
            "MLflow server not reachable at %s: requests are not traced",
            settings.mlflow_tracking_uri,
        )
    version()
    # A profile that runs its model inside the process (the demo) loads it now
    harness.prepare()


def health() -> Health:
    return Health("ok")


def installed_version() -> str:
    # The demo Space runs the code from its files without installing the package, so the
    # version is unknown there, like the Git commit where Git is missing
    try:
        return package_version("multiagent-ai-lab")
    except PackageNotFoundError:
        return "unknown"


@lru_cache
def version() -> VersionInfo:
    # Fixed at the first call: a running program keeps the code, configs and prompts it loaded
    profile = get_settings().profile
    parts = tracing.pipeline_parts(profile)
    return VersionInfo(
        package=installed_version(),
        profile=profile,
        git_commit=parts["git_commit"],
        git_dirty=parts["git_dirty"] == "true",
        pipeline_version=tracing.pipeline_version(parts),
    )


def models() -> ProfileModels:
    # Reads configs/models.yaml only. No model client is created
    profile = get_settings().profile
    entry = load_models().get(profile)
    found = entry.models.items() if entry else []
    return ProfileModels(
        profile,
        [ModelInfo(role, ref.name, ref.source or ref.name, ref.revision) for role, ref in found],
    )


def chat(message: str, history: list[Turn]) -> Events:
    return harness.run(harness.Request(message, history), ROUTES)


# Saved chats


TITLE_LENGTH = 80


class ChatNotFound(Exception):
    # Also for a chat of someone else, so the IDs of other chats are never confirmed
    pass


class GuestLimitReached(Exception):
    pass


@dataclass(frozen=True)
class Owner:
    # Whose chats a request may use: a user's or a guest session's. Exactly one is set
    user_id: int | None = None
    session_id: int | None = None

    def __post_init__(self) -> None:
        if (self.user_id is None) == (self.session_id is None):
            raise ValueError("an owner is a user or a guest session")

    def owns(self) -> ColumnElement[bool]:
        if self.user_id is not None:
            return db.Chat.user_id == self.user_id
        return db.Chat.session_id == self.session_id


@dataclass(frozen=True)
class ChatSummary:
    id: uuid.UUID
    title: str
    updated_at: datetime


@dataclass(frozen=True)
class ChatMessage:
    id: int
    role: str
    content: str
    status: str
    created_at: datetime
    # The answer as safe HTML from its Markdown (filled in by the API)
    html: str | None = None


@dataclass(frozen=True)
class ChatDetail:
    id: uuid.UUID
    title: str
    updated_at: datetime
    messages: list[ChatMessage]


def open_database() -> None:
    # Called when the API starts: a database without the latest migration stops the start.
    # Sessions past their time limits are removed
    if not db.schema_is_current():
        raise RuntimeError("The app database is not up to date. Run: uv run alembic upgrade head")
    with db.get_sessionmaker()() as s:
        removed = auth.remove_expired_sessions(s)
        s.commit()
    log.info("Removed %d ended sessions", removed)


def title_from(message: str) -> str:
    # The first line of the first message
    line = next((line.strip() for line in message.splitlines() if line.strip()), "")
    if len(line) > TITLE_LENGTH:
        return line[: TITLE_LENGTH - 1].rstrip() + "…"
    return line or "New chat"


def summary(chat: db.Chat) -> ChatSummary:
    return ChatSummary(chat.id, chat.title, chat.updated_at)


def list_chats(s: Session, owner: Owner) -> list[ChatSummary]:
    query = select(db.Chat).where(owner.owns()).order_by(db.Chat.updated_at.desc(), db.Chat.id)
    return [summary(chat) for chat in s.scalars(query)]


def find_chat(s: Session, owner: Owner, chat_id: uuid.UUID) -> db.Chat:
    chat = s.scalar(select(db.Chat).where(db.Chat.id == chat_id, owner.owns()))
    if chat is None:
        raise ChatNotFound
    return chat


def get_chat(s: Session, owner: Owner, chat_id: uuid.UUID) -> ChatDetail:
    chat = find_chat(s, owner, chat_id)
    query = select(db.Message).where(db.Message.chat_id == chat.id).order_by(db.Message.id)
    messages = [
        ChatMessage(row.id, row.role, row.content, row.status, row.created_at)
        for row in s.scalars(query)
    ]
    return ChatDetail(chat.id, chat.title, chat.updated_at, messages)


def rename_chat(s: Session, owner: Owner, chat_id: uuid.UUID, title: str) -> ChatSummary:
    chat = find_chat(s, owner, chat_id)
    chat.title = title
    return summary(chat)


def delete_chat(s: Session, owner: Owner, chat_id: uuid.UUID) -> None:
    # Its messages go with it (the database deletes them)
    s.delete(find_chat(s, owner, chat_id))


def delete_all_chats(s: Session, owner: Owner) -> int:
    result = s.execute(delete(db.Chat).where(owner.owns()))
    return int(getattr(result, "rowcount", 0) or 0)


def count_guest_message(s: Session, browser: db.BrowserSession) -> None:
    # A guest has a limited number of messages per session. The day counts are for the admins
    if browser.guest_messages >= admin.settings(s)["guest_limit"]:
        raise GuestLimitReached
    browser.guest_messages += 1
    today = db.utcnow().date()
    day = s.get(db.GuestDay, today)
    if day is None:
        s.add(db.GuestDay(day=today, messages=1))
    else:
        day.messages += 1


def start_turn(
    s: Session, owner: Owner, chat_id: uuid.UUID | None, message: str
) -> tuple[uuid.UUID, str, list[Turn]]:
    # Opens the chat (a new one without an ID), reads its earlier turns and saves the message.
    # Returns the chat's ID and title and the earlier turns for the harness
    if chat_id is None:
        chat = db.Chat(
            user_id=owner.user_id, session_id=owner.session_id, title=title_from(message)
        )
        s.add(chat)
        s.flush()
        history: list[Turn] = []
    else:
        chat = find_chat(s, owner, chat_id)
        history = memory.history(s, chat.id)
    memory.save_turn(s, chat.id, "user", message)
    chat.updated_at = db.utcnow()
    return chat.id, chat.title, history


def finish_turn(chat_id: uuid.UUID, answer: str, status: str) -> None:
    # Saves the answer when its stream ends: done, stopped early or failed. It has its own
    # database session, because the request's session is closed by then
    with db.get_sessionmaker()() as s:
        chat = s.get(db.Chat, chat_id)
        if chat is None:
            # Deleted while the answer was streaming
            return
        memory.save_turn(s, chat_id, "assistant", answer, status)
        chat.updated_at = db.utcnow()
        s.commit()


# Account of a logged-in user


def set_name(user: db.User, name: str) -> str:
    name = name.strip()
    if not 1 <= len(name) <= 60:
        raise auth.AccountError("name_invalid")
    user.name = name
    return name


def export_chats(s: Session, user: db.User) -> dict[str, Any]:
    # All chats of the user with every message, newest chat first
    chats = []
    for chat in s.scalars(
        select(db.Chat).where(db.Chat.user_id == user.id).order_by(db.Chat.updated_at.desc())
    ):
        query = select(db.Message).where(db.Message.chat_id == chat.id).order_by(db.Message.id)
        chats.append(
            {
                "title": chat.title,
                "updated_at": chat.updated_at.isoformat(timespec="seconds"),
                "messages": [
                    {
                        "role": row.role,
                        "text": row.content,
                        "status": row.status,
                        "time": row.created_at.isoformat(timespec="seconds"),
                    }
                    for row in s.scalars(query)
                ],
            }
        )
    return {
        "exported_at": db.utcnow().isoformat(timespec="seconds"),
        "user": {"name": user.name, "email": user.email},
        "chats": chats,
    }


def delete_account(s: Session, user: db.User, password: str) -> None:
    # Needs the password. The last active admin cannot go. Sessions, chats and messages go
    # with the account (the database deletes them)
    if not auth.verify_password(user.password_hash, password):
        raise auth.AccountError("password_wrong")
    if user.role == "admin":
        admins = s.scalar(
            select(func.count()).where(db.User.role == "admin", db.User.blocked.is_(False))
        )
        if (admins or 0) <= 1:
            raise auth.AccountError("last_admin")
    s.delete(user)


def add_feedback(s: Session, user: db.User, kind: str, message: str) -> None:
    message = message.strip()
    if not message:
        raise auth.AccountError("feedback_empty")
    s.add(db.Feedback(user_id=user.id, kind=kind, message=message))
