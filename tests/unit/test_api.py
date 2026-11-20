# Unit tests for the API and service.py with FastAPI's test client and a fake model, no
# servers. The test client is not used as a context manager, so the start-up of the API
# (tracing to MLflow) does not run here. Saved chats and guests: test_chats.py.

import json
import re
import time
from importlib.metadata import PackageNotFoundError

import anyio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from mrag import api, auth, db, prompts, service, tracing
from mrag.api import app
from mrag.config import Settings
from mrag.harness import loop
from mrag.llm_client import ModelUnavailableError, load_models

client = TestClient(app)


class FakeClient:
    def __init__(self, pieces=("Hel", "lo"), error=None):
        self.pieces, self.error = pieces, error

    def chat_stream(self, messages, role="main", **options):
        with tracing.model_call(role, "fake", {"messages": messages}) as call:
            yield from self.pieces
            if self.error:
                raise self.error
            call.input_tokens, call.output_tokens = 10, 2


@pytest.fixture(autouse=True)
def mac_profile(monkeypatch):
    # The same profile on every computer, whatever its .env says
    settings = Settings(profile="mac")
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(loop, "get_settings", lambda: settings)
    service.version.cache_clear()
    prompts.load.cache_clear()
    yield
    service.version.cache_clear()
    prompts.load.cache_clear()


@pytest.fixture(autouse=True)
def no_cookies():
    client.cookies.clear()
    yield
    client.cookies.clear()


@pytest.fixture
def member(database):
    # Logs the test client in as a member and returns the header with the session's token
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, "ada@example.org", "Ada", "correct horse battery staple")
        token, row = auth.start_session(s, user)
        headers = {auth.CSRF_HEADER: row.csrf_token}
        s.commit()
    client.cookies.set(auth.COOKIE, token)
    return headers


def events(response):
    # Server-Sent Events: "event: name" and "data: json" lines, one blank line after each
    found = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        found.append((lines["event"], json.loads(lines["data"])))
    return found


def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    data = client.get("/v1/version").json()
    assert data["package"] == "0.1.0"
    assert data["profile"] == "mac"
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", data["git_commit"])
    assert re.fullmatch(r"p-[0-9a-f]{12}", data["pipeline_version"])
    assert isinstance(data["git_dirty"], bool)


def test_version_without_the_installed_package(monkeypatch):
    # The demo Space has the code as files only. It must still start
    def missing(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr(service, "package_version", missing)
    assert service.version().package == "unknown"


def test_models_need_a_login(database):
    assert client.get("/v1/models").json() == {"detail": "login_required"}


def test_models_of_the_active_profile(member):
    data = client.get("/v1/models").json()
    expected = load_models()["mac"].models
    assert data["profile"] == "mac"
    assert {model["role"]: model["name"] for model in data["models"]} == {
        role: ref.name for role, ref in expected.items()
    }
    # Only names and versions, never the file fingerprints
    assert all(set(model) == {"role", "name", "source", "revision"} for model in data["models"])


def test_a_profile_without_models_lists_none(member, monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(profile="company"))
    assert client.get("/v1/models").json() == {"profile": "company", "models": []}


def test_chat_streams_the_chat_the_answer_then_the_totals(member, monkeypatch):
    monkeypatch.setattr(loop, "get_client", lambda: FakeClient())
    response = client.post("/v1/chat", json={"message": "Hi"}, headers=member)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    found = events(response)
    name, opened = found[0]
    assert name == "chat" and opened["title"] == "Hi"
    assert found[1:3] == [("delta", {"text": "Hel"}), ("delta", {"text": "lo"})]
    name, done = found[3]
    assert name == "done"
    assert (done["answer"], done["model_calls"], done["input_tokens"], done["output_tokens"]) == (
        "Hello",
        1,
        10,
        2,
    )


def test_an_unreachable_model_gives_one_error_event(member, monkeypatch):
    monkeypatch.setattr(
        loop, "get_client", lambda: FakeClient(pieces=(), error=ModelUnavailableError("down"))
    )
    response = client.post("/v1/chat", json={"message": "Hi"}, headers=member)
    found = events(response)
    assert [name for name, _ in found] == ["chat", "error"]
    assert found[1] == ("error", {"kind": "model_unavailable", "message": "down"})


def test_an_empty_message_is_rejected(member):
    assert client.post("/v1/chat", json={"message": ""}, headers=member).status_code == 422


def test_the_documentation_lists_the_experimental_endpoints():
    spec = client.get("/openapi.json").json()
    assert sorted(spec["paths"]) == [
        "/v1/admin/feedback",
        "/v1/admin/feedback/{feedback_id}",
        "/v1/admin/log",
        "/v1/admin/settings",
        "/v1/admin/stats",
        "/v1/admin/users",
        "/v1/admin/users/{user_id}",
        "/v1/admin/users/{user_id}/reset-password",
        "/v1/auth/login",
        "/v1/auth/logout",
        "/v1/auth/signup",
        "/v1/chat",
        "/v1/chats",
        "/v1/chats/{chat_id}",
        "/v1/feedback",
        "/v1/health",
        "/v1/me",
        "/v1/me/delete",
        "/v1/me/export",
        "/v1/me/password",
        "/v1/me/preferences",
        "/v1/models",
        "/v1/version",
    ]
    assert "Experimental" in spec["info"]["description"]


class SlowClient:
    # Writes many pieces slowly and records whether its stream was closed before the end
    def __init__(self):
        self.finished = self.closed = False

    def chat_stream(self, messages, role="main", **options):
        try:
            for number in range(200):
                time.sleep(0.02)
                yield f"{number}\n"
            self.finished = True
        finally:
            self.closed = True


def test_a_closed_connection_closes_the_answer_and_saves_it_as_stopped(member, monkeypatch):
    # Runs the endpoint's response the way the web server does. The client goes away after
    # the first answer piece
    model = SlowClient()
    monkeypatch.setattr(loop, "get_client", lambda: model)
    sent = []

    async def send(message):
        sent.append(message)

    async def receive():
        while not any(b"event: delta" in message.get("body", b"") for message in sent):
            await anyio.sleep(0.01)
        return {"type": "http.disconnect"}

    with db.get_sessionmaker()() as s:
        owner = service.Owner(user_id=s.scalars(select(db.User.id)).one())

        async def serve():
            body = api.ChatRequest(message="Count to 200")
            response = await api.chat(body, s, owner, None)
            scope = {"type": "http", "asgi": {"spec_version": "2.3"}}
            await response(scope, receive, send)

        anyio.run(serve)
    assert model.closed and not model.finished
    with db.get_sessionmaker()() as s:
        answer = s.scalars(select(db.Message).where(db.Message.role == "assistant")).one()
    assert answer.status == "stopped" and answer.content.startswith("0\n")


def test_start_without_mlflow_turns_tracing_off(monkeypatch, caplog):
    monkeypatch.setattr(tracing, "server_reachable", lambda uri=None: False)
    try:
        service.start()
        assert not tracing.enabled()
        assert "not traced" in caplog.text
    finally:
        tracing.setup(Settings(profile="ci"))
