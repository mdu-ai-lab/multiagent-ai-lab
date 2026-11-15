# Adds result bundles from Kaggle and Colab to the Mac's MLflow, each bundle only once.
# A bundle is the folder ops/gpu_smoke.py writes: bundle.json (the run's parameters, metrics,
# tags and times) and files/ (its result files). Colab bundles arrive through make pull-inbox,
# Kaggle bundles are downloaded from the notebook output into data/inbox.
# Run: make pull-inbox, or: uv run python ops/import_runs.py [folder] (needs make mlflow)

import json
import os
import sys
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import Metric, Param
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import PROJECT_ROOT, get_settings

INBOX = PROJECT_ROOT / "data" / "inbox"
BUNDLE_FORMAT = "mrag-run-bundle/1"
# The run ID on Kaggle or Colab. It makes a second import of the same bundle a no-op
SOURCE_TAG = "mrag.source_run_id"
REQUIRED = {"format", "source_run_id", "experiment", "run_name", "status", "start_time", "end_time"}


class BundleError(Exception):
    pass


def read_bundle(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text())
    missing = REQUIRED - set(bundle)
    if bundle.get("format") != BUNDLE_FORMAT or missing:
        raise BundleError(f"{path} is not a result bundle (format or fields {sorted(missing)})")
    return bundle


def already_imported(client: MlflowClient, bundle: dict[str, Any]) -> bool:
    experiment = client.get_experiment_by_name(bundle["experiment"])
    if experiment is None:
        return False
    query = f"tags.`{SOURCE_TAG}` = '{bundle['source_run_id']}'"
    return bool(client.search_runs([experiment.experiment_id], filter_string=query, max_results=1))


def import_bundle(client: MlflowClient, folder: Path) -> str | None:
    # Returns the new run ID. None means the bundle was imported before
    bundle = read_bundle(folder / "bundle.json")
    if already_imported(client, bundle):
        return None
    experiment = client.get_experiment_by_name(bundle["experiment"])
    experiment_id = (
        experiment.experiment_id if experiment else client.create_experiment(bundle["experiment"])
    )
    tags = bundle.get("tags", {}) | {SOURCE_TAG: bundle["source_run_id"]}
    run = client.create_run(
        experiment_id, start_time=bundle["start_time"], tags=tags, run_name=bundle["run_name"]
    )
    run_id = run.info.run_id
    client.log_batch(
        run_id,
        metrics=[
            Metric(key, float(value), bundle["end_time"], 0)
            for key, value in bundle.get("metrics", {}).items()
        ],
        params=[Param(key, str(value)) for key, value in bundle.get("params", {}).items()],
    )
    files = folder / "files"
    if files.is_dir() and any(files.iterdir()):
        client.log_artifacts(run_id, str(files))
    client.set_terminated(run_id, status=bundle["status"], end_time=bundle["end_time"])
    return run_id


def import_all(client: MlflowClient, inbox: Path = INBOX) -> tuple[list[str], int]:
    # Returns the new run IDs and the number of bundles that were already in MLflow
    created, skipped = [], 0
    for path in sorted(inbox.rglob("bundle.json")):
        run_id = import_bundle(client, path.parent)
        if run_id is None:
            skipped += 1
        else:
            created.append(run_id)
    return created, skipped


def main() -> int:
    inbox = Path(sys.argv[1]) if len(sys.argv) > 1 else INBOX
    settings = get_settings()
    # No usage statistics are sent to the MLflow developers
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    if not tracing.server_reachable(settings.mlflow_tracking_uri):
        print("Importing result bundles needs the MLflow server (make mlflow)", file=sys.stderr)
        return 1
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    if not inbox.is_dir():
        print(f"No inbox folder at {inbox}, nothing to import")
        return 0
    try:
        created, skipped = import_all(MlflowClient(), inbox)
    except BundleError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{len(created)} result bundles imported, {skipped} already in MLflow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
