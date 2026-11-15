# Saved chats through the API: each chat belongs to one user or one guest session, earlier turns
# come from the database, every answer is saved with how it ended and nobody reaches the chats
# of someone else. A fake model answers, on a new app database for each test.

import json

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import select

from mrag import auth, db, prompts, service
from mrag.api import app
from mrag.config import Settings
from mrag.harness import loop, memory
from mrag.llm_client import ModelUnavailableError

PASSWORD = "correct horse battery staple"


class RecordingClient:
    # Answers "Fine." and keeps the messages it was sent
    def __init__(self, error=None):
        self.sent, self.error = [], error

    def chat_stream(self, messages, role="main", **options):
        self.sent.append(messages)
        if self.error:
            raise self.error
        yield from ("Fi", "ne.")


@pytest.fixture(autouse=True)
def fake_model(database, monkeypatch):
    model = RecordingClient()
    settings = Settings(profile="mac")
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(loop, "get_settings", lambda: settings)
    monkeypatch.setattr(loop, "get_client", lambda: model)
    prompts.load.cache_clear()
    yield model
    prompts.load.cache_clear()


def browser(email=None, role="member"):
    # A test client with its own session. Without an email it is a guest's session
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, email, "Someone", PASSWORD, role) if email else None
        token, row = auth.start_session(s, user)
        csrf = row.csrf_token
        s.commit()
    client = TestClient(app)
    client.cookies.set(auth.COOKIE, token)
    client.headers[auth.CSRF_HEADER] = csrf
    return client


def send(client, message, chat_id=None):
    # Returns the events of the stream as (name, data) pairs
    response = client.post("/v1/chat", json={"message": message, "chat_id": chat_id})
    if response.status_code != 200:
        return response
    return [
        (lines["event"], json.loads(lines["data"]))
        for block in response.text.strip().split("\n\n")
        for lines in [dict(line.split(": ", 1) for line in block.splitlines())]
    ]


def stored_messages():
    with db.get_sessionmaker()() as s:
        rows = s.scalars(select(db.Message).order_by(db.Message.id))
        return [(row.role, row.content, row.status) for row in rows]


def set_guest_mode(on, limit=5):
    with db.get_sessionmaker()() as s:
        s.merge(db.AppSetting(key="guest_mode", value=on))
        s.merge(db.AppSetting(key="guest_limit", value=limit))
        s.commit()


def test_a_first_message_starts_a_chat_named_after_it():
    ada = browser("ada@example.org")
    found = send(ada, "  \nPlan a trip to Kiruna\nin winter")
    name, opened = found[0]
    assert name == "chat" and opened["title"] == "Plan a trip to Kiruna"
    assert found[-1][0] == "done"
    assert stored_messages() == [
        ("user", "  \nPlan a trip to Kiruna\nin winter", "done"),
        ("assistant", "Fine.", "done"),
    ]
    [listed] = ada.get("/v1/chats").json()
    assert listed["id"] == opened["chat_id"] and listed["title"] == "Plan a trip to Kiruna"


def test_the_next_message_gets_the_earlier_turns_from_the_database(fake_model):
    ada = browser("ada@example.org")
    chat_id = send(ada, "Hello")[0][1]["chat_id"]
    send(ada, "And now?", chat_id)
    sent = [(m["role"], m["content"]) for m in fake_model.sent[-1] if m["role"] != "system"]
    assert sent == [("user", "Hello"), ("assistant", "Fine."), ("user", "And now?")]
    detail = ada.get(f"/v1/chats/{chat_id}").json()
    assert [m["content"] for m in detail["messages"]] == ["Hello", "Fine.", "And now?", "Fine."]


def test_a_failed_answer_is_saved_as_failed_and_left_out_of_the_history(fake_model):
    ada = browser("ada@example.org")
    fake_model.error = ModelUnavailableError("down")
    found = send(ada, "Hello")
    assert [name for name, _ in found] == ["chat", "error"]
    assert stored_messages()[-1] == ("assistant", "", "failed")
    fake_model.error = None
    send(ada, "Again", found[0][1]["chat_id"])
    sent = [(m["role"], m["content"]) for m in fake_model.sent[-1] if m["role"] != "system"]
    assert sent == [("user", "Hello"), ("user", "Again")]


def test_nobody_reaches_the_chats_of_someone_else():
    ada, grace = browser("ada@example.org"), browser("grace@example.org", role="admin")
    chat_id = send(ada, "My own plan")[0][1]["chat_id"]
    # The same answer as for a chat that does not exist, so no chat ID is ever confirmed
    for client in (grace, ada):
        other = chat_id if client is grace else "00000000-0000-4000-8000-000000000000"
        assert client.get(f"/v1/chats/{other}").json() == {"detail": "chat_not_found"}
        assert client.patch(f"/v1/chats/{other}", json={"title": "x"}).status_code == 404
        assert client.delete(f"/v1/chats/{other}").status_code == 404
        assert send(client, "Hi", other).json() == {"detail": "chat_not_found"}
    assert grace.get("/v1/chats").json() == []
    grace.delete("/v1/chats")
    assert len(ada.get("/v1/chats").json()) == 1
    assert stored_messages() == [("user", "My own plan", "done"), ("assistant", "Fine.", "done")]


def test_rename_and_delete_one_chat_or_all():
    ada = browser("ada@example.org")
    first = send(ada, "First")[0][1]["chat_id"]
    second = send(ada, "Second")[0][1]["chat_id"]
    assert [c["id"] for c in ada.get("/v1/chats").json()] == [second, first]
    renamed = ada.patch(f"/v1/chats/{first}", json={"title": "  Trip plan  "}).json()
    assert renamed["title"] == "Trip plan"
    assert ada.patch(f"/v1/chats/{first}", json={"title": "   "}).status_code == 422
    assert ada.patch(f"/v1/chats/{first}", json={"title": "x" * 81}).status_code == 422
    assert ada.delete(f"/v1/chats/{first}").status_code == 204
    assert [c["id"] for c in ada.get("/v1/chats").json()] == [second]
    assert ada.delete("/v1/chats").json() == {"deleted": 1}
    assert ada.get("/v1/chats").json() == [] and stored_messages() == []


def test_changing_a_chat_needs_the_session_token():
    ada = browser("ada@example.org")
    chat_id = send(ada, "Hello")[0][1]["chat_id"]
    del ada.headers[auth.CSRF_HEADER]
    assert ada.post("/v1/chat", json={"message": "Hi"}).json() == {"detail": "forged_request"}
    assert ada.patch(f"/v1/chats/{chat_id}", json={"title": "x"}).status_code == 403
    assert ada.delete(f"/v1/chats/{chat_id}").status_code == 403
    assert ada.delete("/v1/chats").status_code == 403


def test_guests_cannot_chat_while_guest_mode_is_off():
    guest = browser()
    assert send(guest, "Hi").json() == {"detail": "login_required"}
    assert guest.get("/v1/chats").json() == {"detail": "login_required"}
    assert TestClient(app).get("/v1/chats").json() == {"detail": "login_required"}


def test_a_guest_chats_up_to_the_limit_and_the_admins_see_the_count():
    set_guest_mode(True, limit=2)
    guest = browser()
    chat_id = send(guest, "One")[0][1]["chat_id"]
    assert send(guest, "Two", chat_id)[-1][0] == "done"
    assert send(guest, "Three", chat_id).json() == {"detail": "guest_limit"}
    assert len(guest.get(f"/v1/chats/{chat_id}").json()["messages"]) == 4
    with db.get_sessionmaker()() as s:
        assert s.scalars(select(db.GuestDay.messages)).one() == 2


def test_guests_and_users_never_see_each_others_chats():
    set_guest_mode(True)
    guest, ada = browser(), browser("ada@example.org")
    guest_chat = send(guest, "Guest question")[0][1]["chat_id"]
    ada_chat = send(ada, "Ada's question")[0][1]["chat_id"]
    assert [c["id"] for c in guest.get("/v1/chats").json()] == [guest_chat]
    assert [c["id"] for c in ada.get("/v1/chats").json()] == [ada_chat]
    assert guest.get(f"/v1/chats/{ada_chat}").status_code == 404
    assert ada.get(f"/v1/chats/{guest_chat}").status_code == 404


def test_a_blocked_user_is_never_treated_as_a_guest():
    set_guest_mode(True)
    ada = browser("ada@example.org")
    with db.get_sessionmaker()() as s:
        s.scalars(select(db.User)).one().blocked = True
        s.commit()
    assert send(ada, "Hi").json() == {"detail": "login_required"}


def test_an_answer_for_a_chat_deleted_meanwhile_is_dropped():
    ada = browser("ada@example.org")
    chat_id = send(ada, "Hello")[0][1]["chat_id"]
    ada.delete(f"/v1/chats/{chat_id}")
    service.finish_turn(service.uuid.UUID(chat_id), "Late answer", "done")
    assert stored_messages() == []


@pytest.mark.parametrize(
    ("message", "title"),
    [("Hello", "Hello"), ("   ", "New chat"), ("x" * 100, "x" * 79 + "…")],
)
def test_titles(message, title):
    assert service.title_from(message) == title
    assert len(service.title_from(message)) <= service.TITLE_LENGTH


def test_the_history_leaves_out_failed_and_empty_answers(session):
    user = auth.create_user(session, "ada@example.org", "Ada", PASSWORD)
    chat = db.Chat(user_id=user.id, title="Chat")
    session.add(chat)
    session.flush()
    for role, content, status in [
        ("user", "One", "done"),
        ("assistant", "Half an ans", "failed"),
        ("user", "Two", "done"),
        ("assistant", "", "stopped"),
        ("user", "Three", "done"),
        ("assistant", "Partly", "stopped"),
    ]:
        memory.save_turn(session, chat.id, role, content, status)
    turns = [(turn.role, turn.content) for turn in memory.history(session, chat.id)]
    assert turns == [("user", "One"), ("user", "Two"), ("user", "Three"), ("assistant", "Partly")]


def test_an_owner_is_a_user_or_a_guest_session():
    with pytest.raises(ValueError):
        service.Owner()
    with pytest.raises(ValueError):
        service.Owner(user_id=1, session_id=2)


def test_the_api_starts_only_on_an_up_to_date_database(database):
    with db.get_sessionmaker()() as s:
        _, ended = auth.start_session(s, None)
        ended.expires_at = db.utcnow()
        s.commit()
    service.open_database()
    with db.get_sessionmaker()() as s:
        assert s.scalars(select(db.BrowserSession)).all() == []
    command.downgrade(database, "base")
    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        service.open_database()
