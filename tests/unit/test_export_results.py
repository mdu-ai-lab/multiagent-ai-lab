# Unit tests for export_results.py. They use a temporary MLflow database, no server.

import json

from mrag import export_results, tracing


def test_only_published_runs_are_exported_once(store):
    with tracing.run("qa", run_name="public test set", publish=True) as public_id:
        tracing.log_results({"f1": 0.61})
    with tracing.run("qa", run_name="own files"):
        tracing.log_results({"f1": 0.9})
    results = store / "results"
    first = export_results.export(results)
    assert [path.name.endswith(f"_{public_id}.json") for path in first] == [True]
    assert first[0].parent == results / "qa"
    # A second export writes nothing new and never overwrites a file
    assert export_results.export(results) == []


def test_summary_holds_only_numbers_and_versions(store):
    with tracing.run("qa", run_name="public test set", datasets={"qasper": "abc123"}, publish=True):
        tracing.log_results({"f1": 0.61})
    [path] = export_results.export(store / "results")
    data = json.loads(path.read_text())
    assert set(data) == {
        "route",
        "run_id",
        "run_name",
        "started",
        "status",
        "tags",
        "params",
        "metrics",
    }
    assert set(data["tags"]) == {"git_commit", "git_dirty", "mrag.pipeline_version"}
    assert data["metrics"] == {"f1": 0.61}
    assert data["params"]["dataset.qasper"] == "abc123"
    assert data["status"] == "FINISHED"


def test_missing_server_is_reported_at_once():
    # Port 9 on this Mac has no server, so the check fails within the timeout
    assert tracing.server_reachable("http://127.0.0.1:9") is False


def test_local_database_file_counts_as_reachable(tmp_path):
    assert tracing.server_reachable(f"sqlite:///{tmp_path}/mlflow.db") is True
