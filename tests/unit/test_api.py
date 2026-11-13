# Unit tests for the API and service.py with FastAPI's test client and a fake model, no
# servers. The test client is not used as a context manager, so the start-up of the API
# (tracing to MLflow) does not run here.

import json
import re

import pytest
from fastapi.testclient import TestClient

from mrag import prompts, service, tracing
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
    assert data["package"] == "0.0.1"
    assert data["profile"] == "mac"
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", data["git_commit"])
    assert re.fullmatch(r"p-[0-9a-f]{12}", data["pipeline_version"])
    assert isinstance(data["git_dirty"], bool)


def test_models_of_the_active_profile():
    data = client.get("/v1/models").json()
    expected = load_models()["mac"].models
    assert data["profile"] == "mac"
    assert {model["role"]: model["name"] for model in data["models"]} == {
        role: ref.name for role, ref in expected.items()
    }
    # Only names and versions, never the file fingerprints
    assert all(set(model) == {"role", "name", "source", "revision"} for model in data["models"])


def test_a_profile_without_models_lists_none(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(profile="company"))
    assert client.get("/v1/models").json() == {"profile": "company", "models": []}


def test_chat_streams_the_answer_then_the_totals(monkeypatch):
    monkeypatch.setattr(loop, "get_client", lambda: FakeClient())
    response = client.post("/v1/chat", json={"message": "Hi", "history": []})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    found = events(response)
    assert found[:2] == [("delta", {"text": "Hel"}), ("delta", {"text": "lo"})]
    name, done = found[2]
    assert name == "done"
    assert (done["answer"], done["model_calls"], done["input_tokens"], done["output_tokens"]) == (
        "Hello",
        1,
        10,
        2,
    )


def test_an_unreachable_model_gives_one_error_event(monkeypatch):
    monkeypatch.setattr(
        loop, "get_client", lambda: FakeClient(pieces=(), error=ModelUnavailableError("down"))
    )
    response = client.post("/v1/chat", json={"message": "Hi"})
    assert events(response) == [("error", {"kind": "model_unavailable", "message": "down"})]


def test_an_empty_message_is_rejected():
    assert client.post("/v1/chat", json={"message": ""}).status_code == 422


def test_the_documentation_lists_the_experimental_endpoints():
    spec = client.get("/openapi.json").json()
    assert sorted(spec["paths"]) == ["/v1/chat", "/v1/health", "/v1/models", "/v1/version"]
    assert "Experimental" in spec["info"]["description"]


def test_start_without_mlflow_turns_tracing_off(monkeypatch, caplog):
    monkeypatch.setattr(tracing, "server_reachable", lambda uri=None: False)
    try:
        service.start()
        assert not tracing.enabled()
        assert "not traced" in caplog.text
    finally:
        tracing.setup(Settings(profile="ci"))
