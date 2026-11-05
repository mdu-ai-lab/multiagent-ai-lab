# Unit tests for tracing.py. They use a temporary MLflow database, no server.

import mlflow
import pytest

from mrag import tracing
from mrag.config import Settings


def last_trace():
    trace_id = mlflow.get_last_active_trace_id()
    mlflow.flush_trace_async_logging()
    return mlflow.get_trace(trace_id)


def test_request_records_totals_and_token_usage(store):
    with tracing.request("chat", {"question": "hello"}) as totals:
        for input_tokens, output_tokens in [(10, 5), (7, 3)]:
            messages = [{"role": "user", "content": "hi"}]
            with tracing.model_call("main", "qwen3.5-9b", {"messages": messages}) as call:
                call.output, call.input_tokens, call.output_tokens = "ok", input_tokens, output_tokens
        tracing.set_fallback("single_answer")
        totals.output = "answer"
    trace = last_trace()
    assert (totals.model_calls, totals.input_tokens, totals.output_tokens) == (2, 17, 8)
    assert trace.info.token_usage == {"input_tokens": 17, "output_tokens": 8, "total_tokens": 25}
    assert trace.info.trace_metadata["mrag.model_calls"] == "2"
    assert trace.info.trace_metadata["mrag.fallback"] == "single_answer"
    assert int(trace.info.trace_metadata["mrag.duration_ms"]) == totals.duration_ms
    assert [span.span_type for span in trace.data.spans] == ["CHAIN", "CHAT_MODEL", "CHAT_MODEL"]
    assert mlflow.get_experiment(trace.info.experiment_id).name == "chat"


def test_failed_request_is_traced_as_error(store):
    with pytest.raises(ValueError):
        with tracing.request("chat", {"question": "hello"}):
            raise ValueError("model server down")
    assert last_trace().info.state == "ERROR"


def test_images_are_replaced_by_a_short_note():
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    messages = [{"role": "user", "content": [{"type": "text", "text": "page"}, image]}]
    readable = tracing.readable_messages(messages)
    assert readable[0]["content"][1]["image_url"]["url"] == "<image, 26 characters>"
    # The original messages are not changed
    assert messages[0]["content"][1] is image


def test_run_logs_git_commit_config_models_and_datasets(store):
    with tracing.run("chat", run_name="test", datasets={"qasper": "abc123"}) as run_id:
        tracing.log_results({"f1": 0.5})
    data = mlflow.get_run(run_id).data
    assert len(data.tags["git_commit"]) == 40
    assert data.tags["git_dirty"] in ("true", "false")
    assert data.params["profile"] == "mac"
    assert data.params["model.main"] == "qwen3.5-9b"
    assert "config.models.yaml" in data.params
    assert data.params["dataset.qasper"] == "abc123"
    assert data.metrics == {"f1": 0.5}


def test_tracing_is_off_outside_the_mac_profile():
    assert tracing.setup(Settings(profile="ci")) is False
    with tracing.request("chat", {"question": "hello"}) as totals:
        with tracing.model_call("main", "qwen3.5-9b", {}) as call:
            call.input_tokens, call.output_tokens = 2, 1
    # Totals are still counted, but nothing goes to MLflow
    assert (totals.model_calls, totals.input_tokens, totals.output_tokens) == (1, 2, 1)
    with pytest.raises(tracing.TracingError):
        with tracing.run("chat"):
            pass


def test_counters_outside_a_request_do_nothing():
    tracing.setup(Settings(profile="ci"))
    tracing.count_tool_call()
    tracing.set_fallback("refusal")
    with tracing.request("chat", {}) as totals:
        tracing.count_tool_call()
    assert (totals.tool_calls, totals.fallback) == (1, None)


def test_model_call_outside_a_request_is_not_recorded(store):
    before = mlflow.get_last_active_trace_id()
    with tracing.model_call("embedding", "qwen3-vl-embedding-2b", {"texts": ["chunk"]}) as call:
        call.output = {"vectors": 1}
    assert mlflow.get_last_active_trace_id() == before


def test_stopped_and_failed_model_calls_are_kept(store):
    def stream():
        with tracing.model_call("main", "qwen3.5-9b", {"messages": []}) as call:
            pieces = []
            try:
                for piece in ["first", "second"]:
                    pieces.append(piece)
                    yield piece
            finally:
                call.output = "".join(pieces)

    with tracing.request("chat", {"question": "hello"}) as totals:
        answer = stream()
        next(answer)
        # The reader stops after the first piece
        answer.close()
        with pytest.raises(RuntimeError):
            with tracing.model_call("main", "qwen3.5-9b", {"messages": []}):
                raise RuntimeError("model server down")
        totals.output = "partial"
    spans = [span for span in last_trace().data.spans if span.span_type == "CHAT_MODEL"]
    assert totals.model_calls == 2
    assert spans[0].status.status_code == "OK"
    assert spans[0].outputs == "first"
    assert spans[0].attributes["mrag.stopped_early"] is True
    assert spans[1].status.status_code == "ERROR"
