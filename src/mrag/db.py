# Database layer: one SQLAlchemy engine and session factory for the app database and its tables.
# SQLite on the Mac now. PostgreSQL later only needs a different MRAG_DATABASE_URL.
# Alembic tracks every change of the tables (migrations/).

import uuid
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Dialect,
    Engine,
    ForeignKey,
    Index,
    MetaData,
    String,
    Text,
    TypeDecorator,
    create_engine,
    event,
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from mrag.config import PROJECT_ROOT, get_settings

# Fixed names for keys, indexes and checks, so later migrations can find them on every database
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class UtcDateTime(TypeDecorator[datetime]):
    # Every time is stored in UTC. SQLite keeps no time zone, so UTC is added back on reading
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("a time for the database needs a time zone")
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('member', 'admin')", name="role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Saved in lower case by auth.py, so one address cannot sign up twice
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    # Argon2id hash with its own salt and settings (auth.py)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default="member")
    blocked: Mapped[bool] = mapped_column(default=False)
    # Theme, language and chat settings of the page, checked by ui.py before saving
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class BrowserSession(Base):
    # One row per browser: a guest's session or a logged-in user's session (auth.py)
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # SHA-256 of the token in the cookie. The token itself is never stored
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # Empty for a guest
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Every form and every changing request must send this back (against forged requests)
    csrf_token: Mapped[str] = mapped_column(String(64))
    remember: Mapped[bool] = mapped_column(default=False)
    guest_messages: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    # The limit without use is counted from here, the hard limit is expires_at
    last_seen_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)


class Chat(Base):
    # A saved chat. It belongs to a user or to a guest's session. A guest's chat goes with it
    __tablename__ = "chats"
    __table_args__ = (
        CheckConstraint("(user_id IS NULL) <> (session_id IS NULL)", name="one_owner"),
        Index("ix_chats_user_id_updated_at", "user_id", "updated_at"),
    )

    # Random, so a chat's address tells nothing about other chats or how many there are
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class Message(Base):
    # One turn of a chat. harness/memory.py reads them in order to build the history
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="role"),
        CheckConstraint("status IN ('done', 'stopped', 'failed')", name="status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    # An answer can end early (the user stopped it or left the page) or fail
    status: Mapped[str] = mapped_column(String(10), default="done")
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (CheckConstraint("kind IN ('problem', 'idea', 'other')", name="kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Kept when the user is deleted, without the link to them
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)
    done: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow)


class AppSetting(Base):
    # Settings an admin changes on the page: guest mode, the guest message limit and sign-up.
    # A missing key means its default in admin.py
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class AuditEntry(Base):
    # Every admin action. Kept when the admin's account is deleted
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # The admin's email at that time. "Terminal" for python -m mrag.admin
    admin_label: Mapped[str] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(50))
    target: Mapped[str] = mapped_column(String(254), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=utcnow, index=True)


class GuestDay(Base):
    # Guest messages per day (UTC) for the admin dashboard. They stay when guest sessions go
    __tablename__ = "guest_daily"

    day: Mapped[date] = mapped_column(primary_key=True)
    messages: Mapped[int] = mapped_column(default=0)


def _set_sqlite_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
    # SQLite turns foreign keys off by default. WAL mode lets the API read
    # while the background worker writes
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


@lru_cache
def get_engine() -> Engine:
    url = make_url(get_settings().database_url)
    is_sqlite = url.get_backend_name() == "sqlite"

    # SQLite creates the file but not its folder
    if is_sqlite and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url)
    if is_sqlite:
        event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine())


def schema_is_current() -> bool:
    # True when the database has every migration in migrations/. Reading the migration files
    # does not run them
    config = Config(toml_file=PROJECT_ROOT / "pyproject.toml")
    heads = set(ScriptDirectory.from_config(config).get_heads())
    with get_engine().connect() as connection:
        current = set(MigrationContext.configure(connection).get_current_heads())
    return current == heads
