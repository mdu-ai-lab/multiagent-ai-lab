# Writes a JSON summary of every published MLflow run into results/, for the dashboard.
# Only runs marked with tracing.run(..., publish=True) are exported, and only their numbers
# and versions: metrics, parameters, git commit and time. Never traces, texts or files.
# Each run is written once as results/<route>/<date>_<run id>.json and never overwritten.
# Run with: uv run python -m mrag.export_results (needs the MLflow server: make mlflow)

import json
import sys
import urllib.request
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mlflow.entities import Experiment, Run
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import PROJECT_ROOT, get_settings

RESULTS_DIR = PROJECT_ROOT / "results"
# Tags that are safe to publish. Every other tag stays in MLflow
SAFE_TAGS = ("git_commit", "git_dirty")


def all_experiments(client: MlflowClient) -> Iterator[Experiment]:
    page_token = None
    while True:
        page = client.search_experiments(page_token=page_token)
        yield from page
        if not page.token:
            return
        page_token = page.token


def published_runs(client: MlflowClient, experiment_id: str) -> Iterator[Run]:
    query = f"tags.`{tracing.PUBLISH_TAG}` = 'true' and attributes.status = 'FINISHED'"
    page_token = None
    while True:
        page = client.search_runs([experiment_id], filter_string=query, page_token=page_token)
        yield from page
        if not page.token:
            return
        page_token = page.token


def summary(run: Run, route: str) -> dict[str, Any]:
    started = datetime.fromtimestamp(run.info.start_time / 1000, tz=UTC)
    return {"route": route, "run_id": run.info.run_id, "run_name": run.info.run_name,
            "started": started.isoformat(timespec="seconds"), "status": run.info.status,
            "tags": {key: run.data.tags[key] for key in SAFE_TAGS if key in run.data.tags},
            "params": dict(sorted(run.data.params.items())),
            "metrics": dict(sorted(run.data.metrics.items()))}


def export(results_dir: Path = RESULTS_DIR) -> list[Path]:
    # Returns the files written in this call. Runs exported before are skipped
    client = MlflowClient()
    written = []
    for experiment in all_experiments(client):
        for run in published_runs(client, experiment.experiment_id):
            data = summary(run, experiment.name)
            path = results_dir / experiment.name / f"{data['started'][:10]}_{run.info.run_id}.json"
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            written.append(path)
    return written


def server_reachable(tracking_uri: str) -> bool:
    # The MLflow client retries for minutes when the server is down, so check it first
    try:
        with urllib.request.urlopen(f"{tracking_uri}/health", timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def main() -> int:
    settings = get_settings()
    if not tracing.setup(settings) or not server_reachable(settings.mlflow_tracking_uri):
        print("Exporting results needs the mac profile and the MLflow server (make mlflow)",
              file=sys.stderr)
        return 1
    written = export()
    for path in written:
        print(f"written {path.relative_to(PROJECT_ROOT)}")
    print(f"{len(written)} new result files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
