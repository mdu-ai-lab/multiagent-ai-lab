# Tables of the app database and their migration, on a new SQLite file for each test
# (the database fixture in conftest.py).
# The migration must build exactly the tables the code describes. The database itself must
# enforce the rules a bug in the code could break: owners, allowed values and deletes.

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from alembic import command
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from mrag import db

TABLES = {
    "app_settings",
    "audit_log",
    "chats",
    "feedback",
    "guest_daily",
    "messages",
    "sessions",
    "users",
}


def add_user(s: Session, email: str = "ada@example.org") -> db.User:
    user = db.User(email=email, name="Ada", password_hash="not-a-real-hash")
    s.add(user)
    s.flush()
    return user


def add_session(s: Session, user: db.User | None) -> db.BrowserSession:
    browser = db.BrowserSession(
        token_hash=uuid.uuid4().hex * 2,
        user_id=user.id if user else None,
        csrf_token="token",
        expires_at=db.utcnow() + timedelta(hours=12),
    )
    s.add(browser)
    s.flush()
    return browser


def test_migration_builds_every_table(database):
    tables = set(inspect(db.get_engine()).get_table_names())
    assert tables == TABLES | {"alembic_version"}


def test_migration_matches_the_tables_in_the_code(database):
    # Fails when a table changes in db.py without a new migration
    command.check(database)


def test_downgrade_removes_every_table(database):
    command.downgrade(database, "base")
    assert set(inspect(db.get_engine()).get_table_names()) == {"alembic_version"}


def test_deleting_a_user_deletes_their_sessions_chats_and_messages(session):
    user = add_user(session)
    add_session(session, user)
    chat = db.Chat(user_id=user.id, title="First")
    session.add(chat)
    session.flush()
    session.add(db.Message(chat_id=chat.id, role="user", content="Hello"))
    session.add(db.Feedback(user_id=user.id, kind="idea", message="Dark mode"))
    session.add(db.AuditEntry(admin_id=user.id, admin_label=user.email, action="block"))
    session.commit()

    session.delete(user)
    session.commit()

    for table in (db.BrowserSession, db.Chat, db.Message):
        assert session.scalars(select(table)).all() == []
    # Feedback and the activity log stay, without the link to the deleted account
    assert session.scalars(select(db.Feedback.user_id)).one() is None
    assert session.scalars(select(db.AuditEntry.admin_id)).one() is None


def test_deleting_a_guest_session_deletes_its_chats(session):
    guest = add_session(session, None)
    chat = db.Chat(session_id=guest.id, title="Guest chat")
    session.add(chat)
    session.flush()
    session.add(db.Message(chat_id=chat.id, role="user", content="Hi"))
    session.commit()

    session.delete(guest)
    session.commit()

    assert session.scalars(select(db.Chat)).all() == []
    assert session.scalars(select(db.Message)).all() == []


@pytest.mark.parametrize("owners", ["none", "both"])
def test_a_chat_needs_exactly_one_owner(session, owners):
    user = add_user(session)
    guest = add_session(session, None)
    if owners == "none":
        chat = db.Chat(title="Nobody's")
    else:
        chat = db.Chat(user_id=user.id, session_id=guest.id, title="Both")
    session.add(chat)
    with pytest.raises(IntegrityError, match="ck_chats_one_owner"):
        session.flush()


@pytest.mark.parametrize(
    ("row", "check"),
    [
        (lambda: db.User(email="x@example.org", name="X", password_hash="h", role="root"), "role"),
        (lambda: db.Feedback(kind="praise", message="Nice"), "kind"),
    ],
)
def test_the_database_refuses_unknown_values(session, row, check):
    session.add(row())
    with pytest.raises(IntegrityError, match=f"ck_.*_{check}"):
        session.flush()


def test_message_role_and_status_are_checked(session):
    user = add_user(session)
    chat = db.Chat(user_id=user.id, title="Chat")
    session.add(chat)
    session.flush()
    session.add(db.Message(chat_id=chat.id, role="system", content="x"))
    with pytest.raises(IntegrityError, match="ck_messages_role"):
        session.flush()
    session.rollback()

    user = add_user(session)
    chat = db.Chat(user_id=user.id, title="Chat")
    session.add(chat)
    session.flush()
    session.add(db.Message(chat_id=chat.id, role="assistant", content="x", status="lost"))
    with pytest.raises(IntegrityError, match="ck_messages_status"):
        session.flush()


def test_an_email_can_sign_up_only_once(session):
    add_user(session)
    with pytest.raises(IntegrityError, match="users.email"):
        add_user(session)


def test_defaults_of_a_new_user(session):
    user = add_user(session)
    session.commit()
    session.expire_all()
    stored = session.get(db.User, user.id)
    assert stored is not None
    assert (stored.role, stored.blocked, stored.settings, stored.last_login_at) == (
        "member",
        False,
        {},
        None,
    )


def test_times_come_back_in_utc(session):
    user = add_user(session)
    # 22:30 in Stockholm in winter is 21:30 UTC
    user.last_login_at = datetime(2026, 11, 15, 22, 30, tzinfo=timezone(timedelta(hours=1)))
    session.commit()
    session.expire_all()
    stored = session.get(db.User, user.id)
    assert stored is not None
    assert stored.last_login_at == datetime(2026, 11, 15, 21, 30, tzinfo=UTC)
    assert stored.last_login_at.tzinfo == UTC


def test_a_time_without_a_time_zone_is_refused(session):
    user = add_user(session)
    user.last_login_at = datetime(2026, 11, 15, 21, 30)
    with pytest.raises(StatementError, match="needs a time zone"):
        session.flush()
