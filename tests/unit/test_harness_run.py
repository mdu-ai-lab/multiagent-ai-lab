# Unit tests for harness.run() with a fake model client, no model server. The last test reads
# the events the way a web server does, each step in another thread, with MLflow tracing on.

import time

import anyio
import mlflow
import pytest
from starlette.concurrency import iterate_in_threadpool

from mrag import harness, prompts, tracing
from mrag.config import PROJECT_ROOT, Settings
from mrag.harness import context, loop
from mrag.harness.settings import ProfileSettings, for_profile
from mrag.llm_client import LLMError, ModelServerError, ModelUnavailableError


class FakeClient:
    # Streams fixed pieces like the real clients: a generator inside a recorded model call
    def __init__(self, pieces=("Hel", "lo"), error=None, delay=0.0):
        self.pieces, self.error, self.delay = pieces, error, delay
        self.calls = []
        self.finished = self.closed = False

    def chat_stream(self, messages, role="main", *, max_tokens=1024, timeout=None, **options):
        self.calls.append({"messages": messages, "max_tokens": max_tokens, "timeout": timeout})
        try:
            with tracing.model_call(role, "fake", {"messages": messages}) as call:
                for piece in self.pieces:
                    time.sleep(self.delay)
                    yield piece
                if self.error:
                    raise self.error
                call.output, call.input_tokens, call.output_tokens = "".join(self.pieces), 10, 2
            self.finished = True
        finally:
            self.closed = True


def chat(handle):
    return handle.answer()


ROUTES = {"chat": chat}


@pytest.fixture(autouse=True)
def mac_profile(monkeypatch):
    # The same profile on every computer, whatever its .env says
    monkeypatch.setattr(loop, "get_settings", lambda: Settings(profile="mac"))
    prompts.load.cache_clear()
    yield
    prompts.load.cache_clear()


def use(monkeypatch, client):
    monkeypatch.setattr(loop, "get_client", lambda: client)
    return client


def test_the_answer_streams_then_ends_with_the_totals(monkeypatch):
    client = use(monkeypatch, FakeClient())
    events = list(harness.run(harness.Request("Hi"), ROUTES))
    done = events[-1]
    assert events[:-1] == [harness.Delta("Hel"), harness.Delta("lo")]
    assert isinstance(done, harness.Done)
    assert (done.answer, done.model_calls, done.input_tokens, done.output_tokens) == (
        "Hello",
        1,
        10,
        2,
    )
    [call] = client.calls
    system = (PROJECT_ROOT / "configs" / "prompts" / "chat_system.txt").read_text()
    assert call["messages"] == [
        {"role": "system", "content": system},
        {"role": "user", "content": "Hi"},
    ]
    assert call["max_tokens"] == for_profile("mac").answer_tokens
    assert 0 < call["timeout"] <= for_profile("mac").time_limit_s


def test_a_long_history_reaches_the_model_within_the_budget(monkeypatch):
    client = use(monkeypatch, FakeClient())
    history = [
        context.Turn("user" if number % 2 == 0 else "assistant", "word " * 300)
        for number in range(80)
    ]
    list(harness.run(harness.Request("Hi", history), ROUTES))
    messages = client.calls[0]["messages"]
    assert 2 < len(messages) < len(history) + 2
    assert context.prompt_tokens(messages) <= for_profile("mac").prompt_budget


def test_an_unreachable_model_server_gives_one_error(monkeypatch):
    use(monkeypatch, FakeClient(pieces=(), error=ModelUnavailableError("down")))
    assert list(harness.run(harness.Request("Hi"), ROUTES)) == [
        harness.Error("model_unavailable", "down")
    ]


@pytest.mark.parametrize(
    ("error", "kind"),
    [(ModelServerError("out of memory"), "model_error"), (LLMError("bad"), "model_error")],
)
def test_an_error_after_some_pieces_keeps_the_pieces(monkeypatch, error, kind):
    use(monkeypatch, FakeClient(error=error))
    events = list(harness.run(harness.Request("Hi"), ROUTES))
    assert events == [harness.Delta("Hel"), harness.Delta("lo"), harness.Error(kind, str(error))]


def test_a_slow_model_stops_at_the_time_limit(monkeypatch):
    client = use(monkeypatch, FakeClient(pieces=("a", "b", "c"), delay=0.2))
    limits = ProfileSettings(context_tokens=8192, answer_tokens=1024, time_limit_s=0.1)
    monkeypatch.setattr(loop, "for_profile", lambda profile: limits)
    events = list(harness.run(harness.Request("Hi"), ROUTES))
    assert events[0] == harness.Delta("a")
    assert events[-1].kind == "time_limit"
    assert client.closed and not client.finished


def test_an_unknown_route_is_reported(monkeypatch):
    use(monkeypatch, FakeClient())
    [event] = harness.run(harness.Request("Hi", route="nope"), ROUTES)
    assert event == harness.Error("harness_error", "Unknown route 'nope'")


def test_a_reader_that_stops_early_closes_the_model_stream(monkeypatch):
    client = use(monkeypatch, FakeClient(pieces=("a", "b", "c")))
    events = harness.run(harness.Request("Hi"), ROUTES)
    assert next(events) == harness.Delta("a")
    events.close()
    assert client.closed and not client.finished


def test_read_like_a_web_server_the_trace_keeps_its_totals(store, monkeypatch):
    use(monkeypatch, FakeClient())

    async def read():
        return [
            event
            async for event in iterate_in_threadpool(harness.run(harness.Request("Hi"), ROUTES))
        ]

    events = anyio.run(read)
    done = events[-1]
    assert isinstance(done, harness.Done)
    assert (done.answer, done.model_calls, done.input_tokens, done.output_tokens) == (
        "Hello",
        1,
        10,
        2,
    )
    # Traces are written in the background
    mlflow.flush_trace_async_logging()
    [trace] = mlflow.search_traces(locations=[tracing.experiment_id("chat")], return_type="list")
    assert trace.info.state == "OK"
    assert trace.info.trace_metadata["mrag.model_calls"] == "1"
    assert trace.info.trace_metadata["mrag.output_tokens"] == "2"
