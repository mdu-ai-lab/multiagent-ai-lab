# Experiment runs and traces in MLflow (D06, D40). Runs and traces go to the local MLflow
# server in the mac profile. In the gpu profile they go to a database file in the job's work
# folder and reach the Mac as a result bundle (ops/gpu_smoke.py, ops/import_runs.py).
# Every request becomes one trace: a root span with the request totals (tokens in and out,
# model calls, tool calls, time and the fallback used) and one child span per model call.
# MLflow adds up the tokens of the model call spans.

import hashlib
import json
import os
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import SpanType
from mlflow.entities.trace_location import MlflowExperimentLocation
from mlflow.tracing.constant import SpanAttributeKey, TokenUsageKey
from mlflow.tracking import MlflowClient

from mrag.config import PROJECT_ROOT, Settings, get_settings

TRACED_PROFILES = {"mac", "gpu"}
# Runs with this tag set to "true" are exported to results/ and shown on the dashboard
PUBLISH_TAG = "mrag.publish"
CONFIG_DIR = PROJECT_ROOT / "configs"
PROMPTS_DIR = CONFIG_DIR / "prompts"
# Span types for the calls llm_client makes
CHAT = SpanType.CHAT_MODEL
EMBEDDING = SpanType.EMBEDDING
RERANKER = SpanType.RERANKER


class TracingError(Exception):
    pass


@dataclass
class RequestTotals:
    route: str
    model_calls: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    fallback: str | None = None
    # The final answer of the request, shown as the output of the trace
    output: Any = None
    # Prompt name and version of every prompt used in the request
    prompts: dict[str, str] = field(default_factory=dict)

    def metadata(self) -> dict[str, str]:
        # Trace metadata values must be strings. They can be searched in MLflow
        values = {
            "route": self.route,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "fallback": self.fallback or "none",
        }
        metadata = {f"mrag.{key}": str(value) for key, value in values.items()}
        metadata.update({f"mrag.prompt.{name}": version for name, version in self.prompts.items()})
        return metadata


@dataclass
class ModelCall:
    # Filled in by the caller after the model answered
    output: Any = None
    input_tokens: int | None = None
    output_tokens: int | None = None


_enabled = False
_profile = "mac"
_tracking_uri = ""
# Snapshot of the setup this process started with (see pipeline_parts)
_pipeline_parts: dict[str, str] = {}
_pipeline_version = ""
_experiment_ids: dict[str, str] = {}
# The totals of the request that is running in this thread or task
_current: ContextVar[RequestTotals | None] = ContextVar("mrag_request_totals", default=None)


def setup(settings: Settings | None = None) -> bool:
    # Safe to call more than once. Returns True when runs and traces go to MLflow
    global _enabled, _profile, _tracking_uri, _pipeline_parts, _pipeline_version
    settings = settings or get_settings()
    # No usage statistics are sent to the MLflow developers
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    _profile = settings.profile
    _tracking_uri = settings.mlflow_tracking_uri
    _enabled = settings.profile in TRACED_PROFILES
    _experiment_ids.clear()
    if _enabled:
        # A running program keeps the code, configs and prompts it loaded at start, so the
        # start is the moment that describes its results
        _pipeline_parts = pipeline_parts(settings.profile)
        _pipeline_version = pipeline_version(_pipeline_parts)
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.tracing.enable()
    else:
        mlflow.tracing.disable()
    return _enabled


def enabled() -> bool:
    return _enabled


def server_reachable(tracking_uri: str | None = None) -> bool:
    # The MLflow client retries for minutes when the server is down, so check it first.
    # A local database file (tests) has no server and is always reachable
    uri = tracking_uri or _tracking_uri
    if not uri.startswith("http"):
        return True
    try:
        with urllib.request.urlopen(f"{uri}/health", timeout=3) as response:
            return bool(response.status == 200)
    except OSError:
        return False


def experiment_id(route: str) -> str:
    # Each route has its own experiment, created the first time it is used
    if route not in _experiment_ids:
        client = MlflowClient()
        found = client.get_experiment_by_name(route)
        _experiment_ids[route] = found.experiment_id if found else client.create_experiment(route)
    return _experiment_ids[route]


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


@contextmanager
def request(route: str, inputs: dict[str, Any]) -> Iterator[RequestTotals]:
    # One user request. Model and tool calls inside it are added to its totals
    totals = RequestTotals(route)
    token = _current.set(totals)
    start = time.perf_counter()
    try:
        if not _enabled:
            try:
                yield totals
            finally:
                totals.duration_ms = elapsed_ms(start)
            return
        location = MlflowExperimentLocation(experiment_id(route))
        with mlflow.start_span(
            name=route, span_type=SpanType.CHAIN, trace_destination=location
        ) as span:
            span.set_inputs(inputs)
            try:
                yield totals
            finally:
                totals.duration_ms = elapsed_ms(start)
                span.set_outputs(totals.output)
                mlflow.update_current_trace(
                    metadata=totals.metadata() | {"mrag.pipeline_version": _pipeline_version}
                )
    finally:
        _current.reset(token)


def readable_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Page images are replaced by a short note, so traces stay small and readable
    readable = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"<image, {len(part['image_url']['url'])} characters>"},
                }
                if part.get("type") == "image_url"
                else part
                for part in content
            ]
        readable.append({**message, "content": content})
    return readable


def add_tokens(totals: RequestTotals | None, call: ModelCall) -> None:
    if totals is not None:
        totals.input_tokens += call.input_tokens or 0
        totals.output_tokens += call.output_tokens or 0


@contextmanager
def model_call(
    role: str, model: str, inputs: dict[str, Any], span_type: str = CHAT
) -> Iterator[ModelCall]:
    # One call to a model inside a request. The caller fills in the answer and the token
    # counts. Calls outside a request, for example while indexing files, are not recorded
    call = ModelCall()
    totals = _current.get()
    if totals is None:
        yield call
        return
    totals.model_calls += 1
    if not _enabled:
        yield call
        add_tokens(totals, call)
        return
    # A span that is not bound to the current context, so a streamed answer can be read
    # piece by piece and still gets one span with the full time of the call
    span = mlflow.start_span_no_context(
        name=f"model_call.{role}",
        span_type=span_type,
        parent_span=mlflow.get_current_active_span(),
        inputs=inputs,
        attributes={"mrag.role": role, "mrag.model": model},
    )
    try:
        yield call
    except GeneratorExit:
        # The caller stopped reading a streamed answer early. Not an error
        span.end(outputs=call.output, attributes={"mrag.stopped_early": True})
        raise
    except BaseException as error:
        # MLflow takes normal errors. A stop such as Ctrl+C is recorded as text
        span.record_exception(error if isinstance(error, Exception) else repr(error))
        span.end(outputs=call.output, status="ERROR")
        raise
    attributes: dict[str, Any] = {}
    if call.input_tokens is not None and call.output_tokens is not None:
        # MLflow's own token field, so the trace shows the total of all its model calls
        attributes[SpanAttributeKey.CHAT_USAGE] = {
            TokenUsageKey.INPUT_TOKENS: call.input_tokens,
            TokenUsageKey.OUTPUT_TOKENS: call.output_tokens,
            TokenUsageKey.TOTAL_TOKENS: call.input_tokens + call.output_tokens,
        }
    span.end(outputs=call.output, attributes=attributes)
    add_tokens(totals, call)


def count_tool_call() -> None:
    if (totals := _current.get()) is not None:
        totals.tool_calls += 1


def set_fallback(name: str) -> None:
    # The backup path a request took, for example "single_answer" or "refusal"
    if (totals := _current.get()) is not None:
        totals.fallback = name


def record_prompt(name: str, version: str) -> None:
    # The prompt version goes to the running request and to the active run
    if (totals := _current.get()) is not None:
        totals.prompts[name] = version
    if _enabled and mlflow.active_run() is not None:
        mlflow.log_param(f"prompt.{name}", version)


def git_state() -> dict[str, str]:
    # The code version: commit, whether there are uncommitted changes and a fingerprint of
    # them. New files that Git does not track yet count by name only
    def git(*args: str) -> str:
        done = subprocess.run(
            ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
        )
        return done.stdout.strip()

    status = git("status", "--porcelain")
    changes = status + "\n" + git("diff", "HEAD")
    return {
        "git_commit": git("rev-parse", "HEAD") or "unknown",
        "git_dirty": "true" if status else "false",
        "git_changes": hashlib.sha256(changes.encode()).hexdigest()[:12] if status else "none",
    }


def pipeline_parts(profile: str) -> dict[str, str]:
    # Everything that defines the setup: code, profile, configs (models.yaml holds the
    # model revisions and file fingerprints) and prompts
    parts = git_state() | {"profile": profile}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        parts[f"config.{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    for path in sorted(PROMPTS_DIR.glob("*.txt")):
        parts[f"prompt_file.{path.stem}"] = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    return parts


def pipeline_version(parts: dict[str, str]) -> str:
    # One short name for the whole setup. Any change in a part gives a new name
    text = json.dumps(parts, sort_keys=True)
    return "p-" + hashlib.sha256(text.encode()).hexdigest()[:12]


def model_params(profile: str) -> dict[str, str]:
    # Imported here because llm_client records its model calls through this module
    from mrag.llm_client import load_models

    params = {}
    entry = load_models().get(profile)
    for role, ref in entry.models.items() if entry else []:
        params[f"model.{role}"] = ref.name
        if ref.revision:
            params[f"model.{role}.source"] = f"{ref.source or ref.name}@{ref.revision}"
        if ref.files:
            params[f"model.{role}.files"] = ", ".join(
                f"{file_name}={digest[:12]}" for file_name, digest in sorted(ref.files.items())
            )
    return params


@contextmanager
def run(
    route: str,
    run_name: str | None = None,
    datasets: dict[str, str] | None = None,
    publish: bool = False,
    profile_models: bool = True,
) -> Iterator[str]:
    # One experiment run, for example an evaluation. Yields the run ID. publish=True only
    # for runs on public test sets: their metrics go to GitHub and the dashboard. The run
    # name is published too, so it must not contain private information. profile_models=False
    # for a run that records its own model, for example a GPU smoke test of a candidate
    if not _enabled:
        raise TracingError("MLflow runs are only logged in the mac profile")
    # Tags and parameters come from the same snapshot as the pipeline version
    git_parts = {key: value for key, value in _pipeline_parts.items() if key.startswith("git_")}
    tags = git_parts | {
        "mrag.pipeline_version": _pipeline_version,
        PUBLISH_TAG: "true" if publish else "false",
    }
    with mlflow.start_run(
        experiment_id=experiment_id(route), run_name=run_name, tags=tags
    ) as active:
        params = {key: value for key, value in _pipeline_parts.items() if key not in git_parts}
        if profile_models:
            params.update(model_params(_profile))
        params.update({f"dataset.{name}": version for name, version in (datasets or {}).items()})
        mlflow.log_params(params)
        yield active.info.run_id


def log_results(metrics: dict[str, float], files: list[Path] | None = None) -> None:
    # Metrics and result files of the active run
    mlflow.log_metrics(metrics)
    for path in files or []:
        mlflow.log_artifact(str(path))
