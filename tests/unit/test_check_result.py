# Unit tests for ops/check_result.py. They use made-up runs and files, no Git and no MLflow.

import hashlib
import importlib.util

import pytest

from mrag import tracing
from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location(
    "check_result", PROJECT_ROOT / "ops" / "check_result.py"
)
check_result = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_result)

DIGEST = "a" * 64
MODELS = (
    f"mac:\n  backend: openai_server\n  models:\n    main:\n      name: m\n"
    f"      source: s/m\n      revision: {'b' * 40}\n"
    f"      files:\n        m.gguf: {DIGEST}\n"
)
PROMPT = "Answer {{question}}"
FILES = {"configs/models.yaml": MODELS.encode(), "configs/prompts/qa.txt": PROMPT.encode()}


def short(data):
    return hashlib.sha256(data).hexdigest()[:12]


def recorded_run(**changes):
    # A run as tracing.run records it, built from the files above
    tags = {"git_commit": "c" * 40, "git_dirty": "false", "git_changes": "none"}
    params = {
        "profile": "mac",
        "config.models.yaml": short(FILES["configs/models.yaml"]),
        "prompt_file.qa": short(FILES["configs/prompts/qa.txt"]),
        "prompt.qa": "1",
        "model.main.files": f"m.gguf={DIGEST[:12]}",
    }
    parts = tags | {
        key: value
        for key, value in params.items()
        if key == "profile" or key.startswith(("config.", "prompt_file."))
    }
    tags["mrag.pipeline_version"] = tracing.pipeline_version(parts)
    for key, value in changes.items():
        (tags if key.startswith(("git_", "mrag.")) else params)[key] = value
    return tags, params


def statuses(tags, params, commit_found=True, prompt_text=PROMPT):
    checks = check_result.check_run(
        tags, params, commit_found, FILES.get, lambda name, version: prompt_text
    )
    return {check.name: check.status for check in checks}


def test_a_correct_run_passes_every_check():
    result = statuses(*recorded_run())
    assert set(result.values()) == {"OK"}
    assert {
        "git commit",
        "configs/models.yaml",
        "configs/prompts/qa.txt",
        "prompt qa version 1",
        "model main files",
        "pipeline version",
    } <= set(result)


def test_unknown_commit_fails():
    assert statuses(*recorded_run(), commit_found=False) == {"git commit": "FAIL"}


@pytest.mark.parametrize("key", ["config.models.yaml", "model.main.files"])
def test_a_changed_record_fails(key):
    result = statuses(*recorded_run(**{key: "000000000000"}))
    assert "FAIL" in result.values()


def test_wrong_pipeline_version_fails():
    result = statuses(*recorded_run(**{"mrag.pipeline_version": "p-000000000000"}))
    assert result["pipeline version"] == "FAIL"


def test_prompt_text_that_differs_from_the_file_fails():
    assert statuses(*recorded_run(), prompt_text="Other text")["prompt qa version 1"] == "FAIL"


CANDIDATES = (
    f"candidates:\n  k-vllm:\n    source: s/m\n    revision: {'b' * 40}\n"
    f"    files:\n        m.safetensors: {DIGEST}\n"
)


def candidate_statuses(changes):
    # A GPU smoke test run: it records the model of its candidate, not of its profile
    files = FILES | {"configs/gpu_candidates.yaml": CANDIDATES.encode()}
    tags, params = recorded_run()
    params |= {
        "profile": "gpu",
        "candidate": "k-vllm",
        "model.source": f"s/m@{'b' * 40}",
        "model.files": f"m.safetensors={DIGEST[:12]}",
    } | changes
    checks = check_result.check_run(tags, params, True, files.get, lambda name, version: PROMPT)
    return {check.name: check.status for check in checks}


def test_a_gpu_smoke_run_is_checked_against_its_candidate():
    result = candidate_statuses({})
    assert result["candidate model"] == "OK"
    assert "models" not in result


@pytest.mark.parametrize(
    "change",
    [
        {"model.files": "m.safetensors=000000000000"},
        {"model.source": f"s/other@{'b' * 40}"},
        {"candidate": "unknown"},
    ],
)
def test_a_gpu_smoke_run_with_another_model_fails(change):
    assert candidate_statuses(change)["candidate model"] == "FAIL"


def test_uncommitted_changes_turn_differences_into_warnings():
    tags, params = recorded_run(git_dirty="true", git_changes="123456789abc")
    params["config.models.yaml"] = "000000000000"
    result = statuses(tags, params)
    assert result["uncommitted changes"] == "WARNING"
    assert result["configs/models.yaml"] == "WARNING"
