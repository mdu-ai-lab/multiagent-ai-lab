# Real checks of the API and the agent harness with the Mac model server (llama-swap). The
# trace check also needs the MLflow server. Start them first, then: uv run pytest -m mac

import json
import urllib.request

import mlflow
import pytest
from fastapi.testclient import TestClient

from mrag import harness, prompts, service, tracing
from mrag.api import app
from mrag.config import get_settings
from mrag.harness import context, settings
from mrag.llm_client import get_client

SETTINGS = get_settings()
QUESTION = "What is the capital of Sweden? Answer in one short sentence."


def reachable(url):
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.mac,
    pytest.mark.skipif(
        not reachable(f"{SETTINGS.model_server_url}/models"), reason="llama-swap is not running"
    ),
]


@pytest.fixture(autouse=True)
def fresh():
    get_client.cache_clear()
    prompts.load.cache_clear()
    yield
    prompts.load.cache_clear()


def test_the_token_count_equals_the_model_servers_count():
    # Swedish, an emoji, extra spaces and earlier turns, counted by us and by llama.cpp
    messages = [
        {"role": "system", "content": prompts.load("chat_system").template},
        {"role": "user", "content": "Hej! Vad är huvudstaden i Sverige? 🇸🇪 "},
        {"role": "assistant", "content": "  Stockholm.\n"},
        {"role": "user", "content": "And 17 times 3?"},
    ]
    result = get_client("mac").chat(messages, max_tokens=1)
    assert result.usage is not None
    assert result.usage.prompt_tokens == context.prompt_tokens(messages)


def test_the_api_streams_a_real_answer():
    response = TestClient(app).post("/v1/chat", json={"message": QUESTION})
    found = [
        dict(line.split(": ", 1) for line in block.splitlines())
        for block in response.text.strip().split("\n\n")
    ]
    names = [event["event"] for event in found]
    assert names[-1] == "done" and set(names[:-1]) == {"delta"}
    done = json.loads(found[-1]["data"])
    assert "Stockholm" in done["answer"]
    # The model server counted exactly the prompt the harness built
    system = prompts.load("chat_system").format()
    budget = settings.for_profile(SETTINGS.profile).prompt_budget
    built = context.build_messages(system, [], QUESTION, budget)
    assert done["input_tokens"] == context.prompt_tokens(built)
    assert done["output_tokens"] > 0 and done["model_calls"] == 1


@pytest.mark.skipif(
    not reachable(f"{SETTINGS.mlflow_tracking_uri}/health"), reason="MLflow is not running"
)
def test_closing_the_stream_stops_the_model_call():
    assert tracing.setup(SETTINGS)
    try:
        events = service.chat("Count slowly from 1 to 200, one number per line.", [])
        assert isinstance(next(events), harness.Delta)
        events.close()
        trace_id = mlflow.get_last_active_trace_id()
        mlflow.flush_trace_async_logging()
        spans = mlflow.get_trace(trace_id).data.spans
        [model_span] = [span for span in spans if span.name == "model_call.main"]
        assert model_span.attributes.get("mrag.stopped_early") is True
        # The model server answers the next request normally
        answer = get_client("mac").chat([{"role": "user", "content": QUESTION}], max_tokens=50)
        assert "Stockholm" in answer.text
    finally:
        tracing.setup(SETTINGS.model_copy(update={"profile": "ci"}))
