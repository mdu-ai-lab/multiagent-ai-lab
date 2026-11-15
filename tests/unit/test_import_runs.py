# Unit tests for ops/import_runs.py. A run is recorded and exported as a bundle with
# ops/gpu_smoke.py in one temporary MLflow database and imported into a second one.

import importlib.util
import json

import mlflow
import pytest
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import PROJECT_ROOT, Settings


def load(name):
    # ops/ is a tools folder, not a package, so the scripts are loaded from their file paths
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "ops" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gpu_smoke = load("gpu_smoke")
import_runs = load("import_runs")


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    # A finished run on "Kaggle", exported as a bundle with one result file
    monkeypatch.chdir(tmp_path)
    tracing.setup(Settings(profile="gpu", mlflow_tracking_uri=f"sqlite:///{tmp_path}/gpu.db"))
    answers = tmp_path / "answers.jsonl"
    answers.write_text('{"question": "q", "correct": true}\n')
    try:
        with tracing.run(gpu_smoke.ROUTE, run_name="kaggle-llamacpp-9b-16bit") as run_id:
            mlflow.log_params({"candidate": "kaggle-llamacpp-9b-16bit", "gpu.count": "2"})
            tracing.log_results({"correct": 5.0, "gpu_hours": 0.25}, files=[answers])
        folder = gpu_smoke.export_bundle(run_id, tmp_path / "inbox" / "bundles")
    finally:
        tracing.setup(Settings(profile="ci"))
    return run_id, folder


@pytest.fixture
def mac(tmp_path):
    # The Mac's MLflow, a second database
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path}/mac.db")
    return MlflowClient()


def test_a_bundle_becomes_the_same_run_on_the_mac(bundle, mac, tmp_path):
    source_id, folder = bundle
    created, skipped = import_runs.import_all(mac, tmp_path / "inbox")
    assert skipped == 0
    [run_id] = created
    run = mac.get_run(run_id)
    original = json.loads((folder / "bundle.json").read_text())
    assert run.info.run_name == "kaggle-llamacpp-9b-16bit"
    assert run.info.status == "FINISHED"
    assert run.info.start_time == original["start_time"]
    assert run.data.metrics == {"correct": 5.0, "gpu_hours": 0.25}
    assert run.data.params == original["params"]
    assert run.data.params["profile"] == "gpu"
    assert run.data.tags[import_runs.SOURCE_TAG] == source_id
    assert run.data.tags["mrag.pipeline_version"] == original["tags"]["mrag.pipeline_version"]
    assert [item.path for item in mac.list_artifacts(run_id)] == ["answers.jsonl"]


def test_a_second_import_adds_nothing(bundle, mac, tmp_path):
    import_runs.import_all(mac, tmp_path / "inbox")
    created, skipped = import_runs.import_all(mac, tmp_path / "inbox")
    assert created == []
    assert skipped == 1
    assert len(mac.search_runs([mac.get_experiment_by_name(gpu_smoke.ROUTE).experiment_id])) == 1


def test_a_file_that_is_not_a_bundle_is_refused(tmp_path, mac):
    folder = tmp_path / "inbox" / "other"
    folder.mkdir(parents=True)
    (folder / "bundle.json").write_text(json.dumps({"format": "something else"}))
    with pytest.raises(import_runs.BundleError, match="not a result bundle"):
        import_runs.import_all(mac, tmp_path / "inbox")


def test_both_tools_use_the_same_bundle_format():
    assert gpu_smoke.BUNDLE_FORMAT == import_runs.BUNDLE_FORMAT
