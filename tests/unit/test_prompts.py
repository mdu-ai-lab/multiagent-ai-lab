# Unit tests for prompts.py. Prompt files are written to a temporary folder. The MLflow tests
# use a temporary MLflow database, no server.

import mlflow
import pytest

from mrag import prompts, tracing
from mrag.config import Settings


@pytest.fixture(autouse=True)
def fresh_cache():
    prompts.load.cache_clear()
    yield
    prompts.load.cache_clear()


def write_prompt(folder, name, text):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.txt").write_text(text)
    return folder


def test_without_mlflow_the_version_is_the_file_fingerprint(tmp_path):
    tracing.setup(Settings(profile="ci"))
    folder = write_prompt(tmp_path / "prompts", "qa-answer", "Answer {{question}} from {{sources}}")
    prompt = prompts.load("qa-answer", folder)
    assert prompt.version == f"file-{prompts.fingerprint(prompt.template)[:12]}"
    assert prompt.variables == {"question", "sources"}
    assert prompt.format(question="Q", sources="S1") == "Answer Q from S1"


def test_missing_value_and_missing_file_are_reported(tmp_path):
    tracing.setup(Settings(profile="ci"))
    folder = write_prompt(tmp_path / "prompts", "qa-answer", "Answer {{question}}")
    with pytest.raises(prompts.PromptError, match="missing values"):
        prompts.load("qa-answer", folder).format()
    with pytest.raises(prompts.PromptError, match="No prompt file"):
        prompts.load("unknown", folder)


def test_changed_text_becomes_a_new_mlflow_version(store):
    folder = write_prompt(store / "prompts", "qa-answer", "Answer {{question}}")
    assert prompts.load("qa-answer", folder).version == "1"
    # The same text again reuses the version
    prompts.load.cache_clear()
    assert prompts.load("qa-answer", folder).version == "1"
    write_prompt(folder, "qa-answer", "Answer only from the sources: {{question}}")
    prompts.load.cache_clear()
    assert prompts.load("qa-answer", folder).version == "2"


def test_prompt_version_is_recorded_in_the_trace(store):
    folder = write_prompt(store / "prompts", "qa-answer", "Answer {{question}}")
    with tracing.request("qa", {"question": "Q"}) as totals:
        prompts.load("qa-answer", folder).format(question="Q")
        totals.output = "answer"
    trace_id = mlflow.get_last_active_trace_id()
    mlflow.flush_trace_async_logging()
    assert mlflow.get_trace(trace_id).info.trace_metadata["mrag.prompt.qa-answer"] == "1"


def test_prompt_version_is_recorded_in_the_run(store):
    folder = write_prompt(store / "prompts", "qa-answer", "Answer {{question}}")
    with tracing.run("qa", run_name="test") as run_id:
        prompts.load("qa-answer", folder).format(question="Q")
    assert mlflow.get_run(run_id).data.params["prompt.qa-answer"] == "1"
