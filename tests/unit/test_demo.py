# Unit tests for the chat logic of the live demo (demo/chat.py), harness.prepare() and the git
# state without Git. They need no Gradio, so they run in CI. The page itself is checked with
# make demo on the Mac and on the Space.

import importlib.util
import subprocess

import pytest

from mrag import harness, prompts, tracing
from mrag.config import PROJECT_ROOT, Settings
from mrag.harness import loop
from mrag.harness.context import Turn
from mrag.llm_client import (
    ModelServerError,
    ModelUnavailableError,
    OpenAIServerClient,
    TransformersClient,
)

# demo/ is not a package, so the module is loaded from its file path
spec = importlib.util.spec_from_file_location("chat", PROJECT_ROOT / "demo" / "chat.py")
chat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat)


class FakeClient:
    def __init__(self, pieces=("Stock", "holm", "."), error=None):
        self.pieces, self.error = pieces, error
        self.messages = None

    def chat_stream(self, messages, role="main", **options):
        self.messages = messages
        with tracing.model_call(role, "fake", {}) as call:
            yield from self.pieces
            if self.error:
                raise self.error
            call.input_tokens, call.output_tokens = 5, 3


@pytest.fixture(autouse=True)
def mac_profile(monkeypatch):
    monkeypatch.setattr(loop, "get_settings", lambda: Settings(profile="mac"))
    prompts.load.cache_clear()
    yield
    prompts.load.cache_clear()


def gradio_turn(role, text):
    # A turn as Gradio 6.32.0 hands it to the chat function (checked in the prototype)
    return {"role": role, "metadata": None, "content": [{"text": text, "type": "text"}]}


def test_text_of_reads_text_parts_and_plain_text():
    assert chat.text_of([{"type": "text", "text": "Hej"}, {"type": "text", "text": "!"}]) == "Hej!"
    assert chat.text_of("plain") == "plain"
    assert chat.text_of([{"type": "file", "file": {"path": "a.pdf"}}]) == ""
    assert chat.text_of(None) == ""


def test_turns_from_keeps_user_and_assistant_turns_with_text():
    history = [
        gradio_turn("user", "Hej!"),
        gradio_turn("assistant", "Hej hej."),
        gradio_turn("assistant", "   "),
        {"role": "user", "content": [{"type": "file", "file": {"path": "a.pdf"}}]},
        gradio_turn("system", "ignored"),
    ]
    assert chat.turns_from(history) == [Turn("user", "Hej!"), Turn("assistant", "Hej hej.")]


def test_answer_streams_the_growing_text_with_the_history(monkeypatch):
    model = FakeClient()
    monkeypatch.setattr(loop, "get_client", lambda: model)
    steps = list(chat.answer("Capital of Sweden?", [gradio_turn("user", "Hej!")]))
    assert steps == ["Stock", "Stockholm", "Stockholm."]
    assert [message["role"] for message in model.messages] == ["system", "user", "user"]
    assert model.messages[1]["content"] == "Hej!"


def test_an_error_keeps_the_shown_text_and_says_why(monkeypatch):
    monkeypatch.setattr(loop, "get_client", lambda: FakeClient(error=ModelServerError("boom")))
    steps = list(chat.answer("Hi", []))
    assert steps[-1] == "Stockholm.\n\n(The answer stopped: boom)"
    monkeypatch.setattr(
        loop, "get_client", lambda: FakeClient(pieces=(), error=ModelUnavailableError("down"))
    )
    assert list(chat.answer("Hi", [])) == ["(The answer stopped: down)"]


def test_prepare_loads_the_model_only_for_the_transformers_backend(monkeypatch):
    loaded = []
    transformers = TransformersClient({})
    monkeypatch.setattr(transformers, "load", lambda role: loaded.append(role))
    monkeypatch.setattr(loop, "get_client", lambda: transformers)
    harness.prepare()
    assert loaded == ["main"]
    server = OpenAIServerClient("http://127.0.0.1:9/v1", {})
    monkeypatch.setattr(loop, "get_client", lambda: server)
    harness.prepare()
    assert loaded == ["main"]


def test_the_git_state_is_unknown_without_git(monkeypatch):
    def no_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", no_git)
    state = tracing.git_state()
    assert state == {"git_commit": "unknown", "git_dirty": "false", "git_changes": "none"}
