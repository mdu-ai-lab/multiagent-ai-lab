# Checks that one MLflow run can be traced back to its exact versions: the git commit, the
# config and prompt files at that commit, the MLflow prompt versions, the pinned model files
# and the pipeline version. Needs the MLflow server (make mlflow).
# Run: uv run python ops/check_result.py <run id>
#  or: uv run python ops/check_result.py --latest <experiment>
# Exit code 0 when no check fails. A run made with uncommitted changes gives warnings,
# because the files in the commit may then differ from what really ran.

import argparse
import hashlib
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

import mlflow
import yaml
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient

from mrag import tracing
from mrag.config import PROJECT_ROOT
from mrag.llm_client import ProfileModels

OK, WARNING, FAIL = "OK", "WARNING", "FAIL"
GIT_KEYS = ("git_commit", "git_dirty", "git_changes")


@dataclass(frozen=True)
class Check:
    status: str
    name: str
    detail: str


def short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, check=False)


def commit_exists(commit: str) -> bool:
    return git("cat-file", "-e", f"{commit}^{{commit}}").returncode == 0


def file_at_commit(commit: str, path: str) -> bytes | None:
    done = git("show", f"{commit}:{path}")
    return done.stdout if done.returncode == 0 else None


def candidate_check(
    candidate: str, params: dict[str, str], read_file: Callable[[str], bytes | None], differs: str
) -> Check:
    # A GPU smoke test run records the model of its candidate in configs/gpu_candidates.yaml,
    # which can differ from the models of its profile
    content = read_file("configs/gpu_candidates.yaml")
    candidates = (yaml.safe_load(content) or {}).get("candidates", {}) if content else {}
    if candidate not in candidates:
        return Check(FAIL, "candidate model", f"{candidate} not in configs/gpu_candidates.yaml")
    entry = candidates[candidate]
    expected = {
        "model.source": f"{entry['source']}@{entry['revision']}",
        "model.files": ", ".join(
            f"{name}={digest[:12]}" for name, digest in sorted(entry["files"].items())
        ),
    }
    wrong = [
        f"{key} recorded {params.get(key) or 'none'}, pinned {value}"
        for key, value in expected.items()
        if params.get(key) != value
    ]
    if wrong:
        return Check(differs, "candidate model", "; ".join(wrong))
    return Check(OK, "candidate model", f"{expected['model.source']}: {expected['model.files']}")


def check_run(
    tags: dict[str, str],
    params: dict[str, str],
    commit_found: bool,
    read_file: Callable[[str], bytes | None],
    prompt_text: Callable[[str, str], str | None],
) -> list[Check]:
    # read_file gives a file as it is in the run's commit. prompt_text gives the text of an
    # MLflow prompt version. Both are passed in, so the checks can be tested without Git or MLflow
    checks: list[Check] = []
    dirty = tags.get("git_dirty") == "true"
    # A difference is an error for a run from committed code, a warning when it had changes
    differs = WARNING if dirty else FAIL

    commit = tags.get("git_commit", "")
    if not commit or not commit_found:
        checks.append(Check(FAIL, "git commit", f"{commit or 'missing'} is not in this repo"))
        return checks
    checks.append(Check(OK, "git commit", commit))
    if dirty:
        checks.append(
            Check(
                WARNING,
                "uncommitted changes",
                f"the run had changes (fingerprint {tags.get('git_changes')}). "
                "Files at the commit may differ from what ran",
            )
        )

    for key, recorded in sorted(params.items()):
        if key.startswith("config."):
            path = f"configs/{key.removeprefix('config.')}"
        elif key.startswith("prompt_file."):
            path = f"configs/prompts/{key.removeprefix('prompt_file.')}.txt"
        else:
            continue
        content = read_file(path)
        if content is None:
            checks.append(Check(differs, path, "not in that commit"))
        elif short_hash(content) != recorded:
            checks.append(
                Check(differs, path, f"recorded {recorded}, commit has {short_hash(content)}")
            )
        else:
            checks.append(Check(OK, path, f"matches the commit ({recorded})"))

    for key, version in sorted(params.items()):
        if not key.startswith("prompt."):
            continue
        name = key.removeprefix("prompt.")
        expected = params.get(f"prompt_file.{name}")
        found: str | None
        if version.startswith("file-"):
            found = version.removeprefix("file-")
        else:
            text = prompt_text(name, version)
            found = short_hash(text.encode()) if text is not None else None
        if found is None:
            checks.append(Check(FAIL, f"prompt {name} version {version}", "not found in MLflow"))
        elif found != expected:
            checks.append(
                Check(
                    FAIL,
                    f"prompt {name} version {version}",
                    f"text fingerprint {found}, prompt file {expected}",
                )
            )
        else:
            checks.append(
                Check(OK, f"prompt {name} version {version}", "same text as the prompt file")
            )

    models_file = read_file("configs/models.yaml")
    profile = params.get("profile", "")
    profiles = yaml.safe_load(models_file) if models_file else {}
    if "candidate" in params:
        checks.append(candidate_check(params["candidate"], params, read_file, differs))
    elif profile in (profiles or {}):
        models = ProfileModels.model_validate(profiles[profile]).models
        for role, ref in sorted(models.items()):
            pinned = ", ".join(
                f"{file_name}={digest[:12]}" for file_name, digest in sorted(ref.files.items())
            )
            recorded = params.get(f"model.{role}.files", "")
            if pinned != recorded:
                checks.append(
                    Check(
                        differs,
                        f"model {role} files",
                        f"recorded {recorded or 'none'}, pinned {pinned or 'none'}",
                    )
                )
            else:
                checks.append(Check(OK, f"model {role} files", pinned or "none pinned"))
    else:
        checks.append(
            Check(FAIL, "models", f"profile {profile or 'missing'} not in configs/models.yaml")
        )

    # The pipeline version is made from the git state, the profile and the file fingerprints
    parts = {key: tags[key] for key in GIT_KEYS if key in tags}
    parts.update(
        {
            key: value
            for key, value in params.items()
            if key == "profile" or key.startswith(("config.", "prompt_file."))
        }
    )
    recomputed = tracing.pipeline_version(parts)
    recorded_version = tags.get("mrag.pipeline_version", "")
    if recomputed == recorded_version:
        checks.append(Check(OK, "pipeline version", recorded_version))
    else:
        checks.append(
            Check(
                FAIL,
                "pipeline version",
                f"recorded {recorded_version or 'missing'}, recomputed {recomputed}",
            )
        )

    datasets = {key: value for key, value in params.items() if key.startswith("dataset.")}
    detail = ", ".join(
        f"{key.removeprefix('dataset.')}={value}" for key, value in sorted(datasets.items())
    )
    checks.append(Check(OK, "datasets", detail or "none recorded"))
    return checks


def mlflow_prompt_text(name: str, version: str) -> str | None:
    try:
        return mlflow.genai.load_prompt(f"prompts:/{name}/{version}", link_to_model=False).template
    except MlflowException:  # a missing prompt or version
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace one MLflow run to its exact versions")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("run_id", nargs="?", help="ID of the run to check")
    target.add_argument(
        "--latest", metavar="EXPERIMENT", help="check the newest run of an experiment"
    )
    args = parser.parse_args()

    if not tracing.setup() or not tracing.server_reachable():
        print(
            "Checking a run needs the mac profile and the MLflow server (make mlflow)",
            file=sys.stderr,
        )
        return 1
    client = MlflowClient()
    run_id = args.run_id
    if args.latest:
        experiment = client.get_experiment_by_name(args.latest)
        runs = (
            client.search_runs(
                [experiment.experiment_id], order_by=["attributes.start_time DESC"], max_results=1
            )
            if experiment
            else []
        )
        if not runs:
            print(f"No run found in experiment {args.latest}", file=sys.stderr)
            return 1
        run_id = runs[0].info.run_id
    run = client.get_run(run_id)
    tags, params = run.data.tags, run.data.params
    commit = tags.get("git_commit", "")
    checks = check_run(
        tags,
        params,
        bool(commit) and commit_exists(commit),
        lambda path: file_at_commit(commit, path),
        mlflow_prompt_text,
    )

    print(f"Run {run_id} ({run.info.run_name})")
    for check in checks:
        print(f"  {check.status:<8} {check.name}: {check.detail}")
    failed = [check for check in checks if check.status == FAIL]
    warned = [check for check in checks if check.status == WARNING]
    if failed:
        print(f"RESULT: FAILED ({len(failed)} failed, {len(warned)} warnings)")
        return 1
    print(f"RESULT: OK ({len(warned)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
