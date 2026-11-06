# Real runs and traces through the local MLflow server and the Mac model server.
# Start both first (make mlflow and llama-swap), then: uv run pytest -m mac

import urllib.request

import mlflow
import pytest
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import get_settings
from mrag.llm_client import get_client

SETTINGS = get_settings()
# Checks from this test go to their own experiment, apart from the real routes
ROUTE = "integration-test"
QUESTION = [{"role": "user", "content": "What is the capital of Sweden? Answer in one short sentence."}]


def reachable(url):
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except OSError:
        return False


pytestmark = [pytest.mark.mac,
              pytest.mark.skipif(not (reachable(f"{SETTINGS.model_server_url}/models")
                                      and reachable(f"{SETTINGS.mlflow_tracking_uri}/health")),
                                 reason="llama-swap or the MLflow server is not running")]


@pytest.fixture(scope="module", autouse=True)
def traced():
    assert tracing.setup(SETTINGS)
    yield
    tracing.setup(SETTINGS.model_copy(update={"profile": "ci"}))


def test_request_trace_on_the_server():
    get_client.cache_clear()
    client = get_client("mac")
    with tracing.request(ROUTE, {"question": QUESTION[0]["content"]}) as totals:
        answer = client.chat(QUESTION, max_tokens=100).text
        streamed = "".join(client.chat_stream(QUESTION, max_tokens=100))
        totals.output = answer
    trace_id = mlflow.get_last_active_trace_id()
    mlflow.flush_trace_async_logging()
    trace = mlflow.get_trace(trace_id)
    assert "Stockholm" in answer and "Stockholm" in streamed
    assert totals.model_calls == 2
    assert trace.info.token_usage["input_tokens"] == totals.input_tokens > 0
    assert trace.info.token_usage["output_tokens"] == totals.output_tokens > 0
    assert trace.info.trace_metadata["mrag.model_calls"] == "2"
    assert [span.span_type for span in trace.data.spans] == ["CHAIN", "CHAT_MODEL", "CHAT_MODEL"]


def test_run_with_a_result_file_on_the_server(tmp_path):
    result = tmp_path / "result.json"
    result.write_text('{"check": true}')
    with tracing.run(ROUTE, run_name="mac check") as run_id:
        tracing.log_results({"check": 1.0}, [result])
    run = mlflow.get_run(run_id)
    # A link instead of a disk path keeps the mlflow folder movable to another computer
    assert run.info.artifact_uri.startswith("mlflow-artifacts:")
    assert [item.path for item in MlflowClient().list_artifacts(run_id)] == ["result.json"]
    assert run.data.params["model.main"] == "qwen3.5-9b"
    assert len(run.data.tags["git_commit"]) == 40
