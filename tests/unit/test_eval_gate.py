# Unit tests for ops/eval_gate.py. They use made-up result files and limits, plus one real
# export from a temporary MLflow database. No server.

import importlib.util
import json

import pytest

from mrag import export_results, tracing
from mrag.config import PROJECT_ROOT

# ops/ is a tools folder, not a package, so the script is loaded from its file path
spec = importlib.util.spec_from_file_location("eval_gate", PROJECT_ROOT / "ops" / "eval_gate.py")
eval_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_gate)

LIMIT = {"route": "qa", "profile": "mac", "dataset": "qasper", "metric": "f1", "min": 0.6}


def write_result(results_dir, run_id, started, f1, profile="mac", dataset="qasper"):
    # A result file as export_results.py writes it
    data = {
        "route": "qa",
        "run_id": run_id,
        "run_name": "public test set",
        "started": started,
        "status": "FINISHED",
        "tags": {},
        "params": {"profile": profile, f"dataset.{dataset}": "abc123"},
        "metrics": {} if f1 is None else {"f1": f1},
    }
    path = results_dir / "qa" / f"{started[:10]}_{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def status(tmp_path, **limit):
    check = eval_gate.check_limit(
        eval_gate.Limit(**LIMIT | limit), eval_gate.load_results(tmp_path)
    )
    return check.status


def test_the_committed_limits_file_is_valid():
    assert isinstance(eval_gate.load_limits(), list)


def test_without_limits_the_gate_passes_and_says_so(tmp_path, monkeypatch, capsys):
    limits = tmp_path / "limits.yaml"
    limits.write_text("limits: []\n")
    monkeypatch.setattr(eval_gate, "LIMITS_FILE", limits)
    monkeypatch.setattr(eval_gate, "RESULTS_DIR", tmp_path / "results")
    assert eval_gate.main() == 0
    assert "RESULT: OK (0 limits)" in capsys.readouterr().out


def test_a_score_within_the_limit_passes(tmp_path):
    write_result(tmp_path, "r1", "2026-11-07T10:00:00+00:00", 0.7)
    assert status(tmp_path) == "OK"


def test_a_score_below_the_minimum_fails(tmp_path):
    write_result(tmp_path, "r1", "2026-11-07T10:00:00+00:00", 0.5)
    assert status(tmp_path) == "FAIL"


def test_a_score_above_the_maximum_fails(tmp_path):
    write_result(tmp_path, "r1", "2026-11-07T10:00:00+00:00", 0.7)
    assert status(tmp_path, min=None, max=0.65) == "FAIL"


def test_only_the_newest_result_counts(tmp_path):
    write_result(tmp_path, "old", "2026-11-06T10:00:00+00:00", 0.9)
    write_result(tmp_path, "new", "2026-11-07T10:00:00+00:00", 0.5)
    assert status(tmp_path) == "FAIL"


def test_results_of_other_profiles_and_datasets_do_not_count(tmp_path):
    write_result(tmp_path, "gpu", "2026-11-07T11:00:00+00:00", 0.1, profile="gpu")
    write_result(tmp_path, "other", "2026-11-07T12:00:00+00:00", 0.1, dataset="tatdqa")
    write_result(tmp_path, "mac", "2026-11-07T10:00:00+00:00", 0.7)
    assert status(tmp_path) == "OK"


@pytest.mark.parametrize("f1", [None, float("nan"), True])
def test_a_missing_or_broken_score_fails(tmp_path, f1):
    write_result(tmp_path, "r1", "2026-11-07T10:00:00+00:00", f1)
    assert status(tmp_path) == "FAIL"


def test_a_real_exported_result_is_read(store):
    # The gate reads exactly the files export_results.py writes from MLflow
    with tracing.run("qa", run_name="public test set", datasets={"qasper": "abc"}, publish=True):
        tracing.log_results({"f1": 0.7})
    export_results.export(store / "results")
    assert status(store / "results") == "OK"
    assert status(store / "results", min=0.8) == "FAIL"


def test_a_limit_without_results_fails(tmp_path):
    assert status(tmp_path) == "FAIL"


@pytest.mark.parametrize(
    "limits",
    [
        [{"route": "qa", "profile": "mac", "dataset": "qasper", "metric": "f1"}],
        [LIMIT | {"min": 0.9, "max": 0.1}],
        [LIMIT | {"unknown": 1}],
        [LIMIT, LIMIT],
    ],
    ids=["no bound", "min above max", "unknown key", "set twice"],
)
def test_an_invalid_limits_file_is_refused(tmp_path, limits):
    path = tmp_path / "limits.yaml"
    path.write_text(json.dumps({"limits": limits}))
    with pytest.raises(eval_gate.EvalGateError, match="not valid"):
        eval_gate.load_limits(path)


def test_the_gate_fails_when_a_limit_breaks(tmp_path, monkeypatch, capsys):
    limits = tmp_path / "limits.yaml"
    limits.write_text(json.dumps({"limits": [LIMIT]}))
    write_result(tmp_path / "results", "r1", "2026-11-07T10:00:00+00:00", 0.5)
    monkeypatch.setattr(eval_gate, "LIMITS_FILE", limits)
    monkeypatch.setattr(eval_gate, "RESULTS_DIR", tmp_path / "results")
    assert eval_gate.main() == 1
    output = capsys.readouterr().out
    assert "FAIL  qa mac qasper f1: 0.5 is below the minimum 0.6" in output
    assert "RESULT: FAIL (1 of 1 limits)" in output
