# Unit tests for llm_client. A small local HTTP server stands in for the model server,
# so no model is needed.

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mrag import llm_client
from mrag.llm_client import (
    InputTooLongError,
    LLMError,
    ModelRef,
    ModelServerError,
    ModelUnavailableError,
    NotSupportedError,
    OpenAIServerClient,
    TransformersClient,
)

MODELS = {role: ModelRef(name=f"{role}-model")
          for role in ("main", "helper", "embedding", "reranker")}


class FakeServer:
    def __init__(self):
        self.requests = []  # (path, body) of every request
        self.replies = {}  # path -> (status, content type, body bytes)
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                server.requests.append((self.path, json.loads(self.rfile.read(length))))
                status, content_type, body = server.replies[self.path]
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def reply(self, path, body, status=200):
        self.replies[path] = (status, "application/json", json.dumps(body).encode())

    def reply_stream(self, path, events):
        text = "".join(f"data: {json.dumps(event)}\n\n" for event in events) + "data: [DONE]\n\n"
        self.replies[path] = (200, "text/event-stream", text.encode())


@pytest.fixture
def server():
    fake = FakeServer()
    yield fake
    fake.httpd.shutdown()


@pytest.fixture
def client(server):
    return OpenAIServerClient(server.url, MODELS, timeout=10, max_retries=0)


def completion(content, reasoning=None):
    message = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {"id": "1", "object": "chat.completion", "created": 0, "model": "main-model",
            "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}}


def test_models_file_is_valid():
    profiles = llm_client.load_models()
    assert profiles["mac"].backend == "openai_server"
    assert set(profiles["mac"].models) == {"main", "helper", "embedding", "reranker"}
    assert profiles["demo"].backend == "transformers"
    assert len(profiles["demo"].models["main"].revision or "") == 40


def test_invalid_models_file_is_rejected(tmp_path):
    path = tmp_path / "models.yaml"
    path.write_text("mac:\n  backend: openai_server\n  models: {main: a}\n  extra: 1\n")
    with pytest.raises(LLMError, match="not valid"):
        llm_client.load_models(path)


def test_profile_without_models_is_reported():
    llm_client.get_client.cache_clear()
    with pytest.raises(LLMError, match="no models"):
        llm_client.get_client("company")


def test_image_part_is_a_data_url():
    part = llm_client.image_part(b"abc")
    assert part == {"type": "image_url", "image_url": {"url": "data:image/png;base64,YWJj"}}


def test_chat_sends_thinking_switch_and_schema(server, client):
    server.reply("/v1/chat/completions", completion('{"city": "Stockholm"}', reasoning="hmm"))
    schema = {"type": "object", "properties": {"city": {"type": "string"}}}
    result = client.chat([{"role": "user", "content": "Where?"}], json_schema=schema,
                         max_tokens=50)
    path, body = server.requests[-1]
    assert path == "/v1/chat/completions"
    assert body["model"] == "main-model"
    assert body["max_tokens"] == 50
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["response_format"]["json_schema"]["schema"] == schema
    assert result.text == '{"city": "Stockholm"}'
    assert result.reasoning == "hmm"
    assert result.usage == llm_client.Usage(12, 3)
    assert result.finish_reason == "stop"


def test_chat_uses_role_model(server, client):
    server.reply("/v1/chat/completions", completion("ok"))
    client.chat([{"role": "user", "content": "hi"}], role="helper", thinking=True)
    body = server.requests[-1][1]
    assert body["model"] == "helper-model"
    assert body["chat_template_kwargs"] == {"enable_thinking": True}
    assert "response_format" not in body


def test_chat_stream_yields_answer_pieces(server, client):
    def event(**delta):
        return {"id": "1", "object": "chat.completion.chunk", "created": 0,
                "model": "main-model", "choices": [{"index": 0, "delta": delta}]}

    server.reply_stream("/v1/chat/completions", [
        event(role="assistant"), event(reasoning_content="thinking"),
        event(content="Hel"), event(content="lo")])
    pieces = list(client.chat_stream([{"role": "user", "content": "hi"}]))
    assert pieces == ["Hel", "lo"]
    assert server.requests[-1][1]["stream"] is True


def test_embed_keeps_input_order(server, client):
    server.reply("/v1/embeddings", {
        "object": "list", "model": "embedding-model",
        "data": [{"object": "embedding", "index": 1, "embedding": [0.0, 1.0]},
                 {"object": "embedding", "index": 0, "embedding": [1.0, 0.0]}],
        "usage": {"prompt_tokens": 4, "total_tokens": 4}})
    assert client.embed(["a", "b"]) == [[1.0, 0.0], [0.0, 1.0]]
    assert server.requests[-1][1]["model"] == "embedding-model"


def test_rerank_returns_best_first(server, client):
    server.reply("/v1/rerank", {"results": [{"index": 0, "relevance_score": 0.2},
                                            {"index": 1, "relevance_score": 0.9}]})
    results = client.rerank("q", ["d0", "d1"])
    assert [(r.index, r.score) for r in results] == [(1, 0.9), (0, 0.2)]
    assert server.requests[-1][1] == {"model": "reranker-model", "query": "q",
                                      "documents": ["d0", "d1"]}


def test_too_long_input_has_its_own_error(server, client):
    # Error body as llama-server sends it
    server.reply("/v1/chat/completions", {"error": {
        "code": 400, "type": "exceed_context_size_error",
        "message": "request (2153 tokens) exceeds the available context size (2048 tokens)"}},
        status=400)
    with pytest.raises(InputTooLongError):
        client.chat([{"role": "user", "content": "long"}])


def test_server_failure_is_a_server_error(server, client):
    server.reply("/v1/chat/completions", {"error": {"code": 500, "message": "Compute error."}},
                 status=500)
    with pytest.raises(ModelServerError):
        client.chat([{"role": "user", "content": "hi"}])


def test_unreachable_server_is_reported():
    unreachable = OpenAIServerClient("http://127.0.0.1:9/v1", MODELS, timeout=2, max_retries=0)
    with pytest.raises(ModelUnavailableError):
        unreachable.chat([{"role": "user", "content": "hi"}])


def test_missing_role_is_reported(server):
    only_main = OpenAIServerClient(server.url, {"main": ModelRef(name="m")}, max_retries=0)
    with pytest.raises(LLMError, match="No model for role 'embedding'"):
        only_main.embed(["a"])


def test_transformers_backend_refuses_what_it_lacks():
    local = TransformersClient({"main": ModelRef(name="unused")})
    with pytest.raises(NotSupportedError):
        local.chat([{"role": "user", "content": "hi"}], json_schema={"type": "object"})
    with pytest.raises(NotSupportedError):
        local.embed(["a"])
    with pytest.raises(NotSupportedError):
        local.rerank("q", ["d"])
