# Experiment runs and traces in MLflow (D06, D40). Runs and traces go to the local MLflow
# server only in the mac profile. Every request becomes one trace: a root span with the
# request totals (tokens in and out, model calls, tool calls, time and the fallback used)
# and one child span per model call. MLflow adds up the tokens of the model call spans.

import hashlib
import os
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import SpanType
from mlflow.entities.trace_location import MlflowExperimentLocation
from mlflow.tracing.constant import SpanAttributeKey, TokenUsageKey
from mlflow.tracking import MlflowClient

from mrag.config import PROJECT_ROOT, Settings, get_settings

TRACED_PROFILES = {"mac"}
CONFIG_DIR = PROJECT_ROOT / "configs"
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

    def metadata(self) -> dict[str, str]:
        # Trace metadata values must be strings. They can be searched in MLflow
        values = {"route": self.route, "model_calls": self.model_calls,
                  "tool_calls": self.tool_calls, "input_tokens": self.input_tokens,
                  "output_tokens": self.output_tokens, "duration_ms": self.duration_ms,
                  "fallback": self.fallback or "none"}
        return {f"mrag.{key}": str(value) for key, value in values.items()}


@dataclass
class ModelCall:
    # Filled in by the caller after the model answered
    output: Any = None
    input_tokens: int | None = None
    output_tokens: int | None = None


_enabled = False
_profile = "mac"
_experiment_ids: dict[str, str] = {}
# The totals of the request that is running in this thread or task
_current: ContextVar[RequestTotals | None] = ContextVar("mrag_request_totals", default=None)


def setup(settings: Settings | None = None) -> bool:
    # Safe to call more than once. Returns True when runs and traces go to MLflow
    global _enabled, _profile
    settings = settings or get_settings()
    # No usage statistics are sent to the MLflow developers
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    _profile = settings.profile
    _enabled = settings.profile in TRACED_PROFILES
    _experiment_ids.clear()
    if _enabled:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.tracing.enable()
    else:
        mlflow.tracing.disable()
    return _enabled


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
        with mlflow.start_span(name=route, span_type=SpanType.CHAIN,
                               trace_destination=location) as span:
            span.set_inputs(inputs)
            try:
                yield totals
            finally:
                totals.duration_ms = elapsed_ms(start)
                span.set_outputs(totals.output)
                mlflow.update_current_trace(metadata=totals.metadata())
    finally:
        _current.reset(token)


def readable_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Page images are replaced by a short note, so traces stay small and readable
    readable = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            content = [{"type": "image_url",
                        "image_url": {"url": f"<image, {len(part['image_url']['url'])} characters>"}}
                       if part.get("type") == "image_url" else part for part in content]
        readable.append({**message, "content": content})
    return readable


def add_tokens(totals: RequestTotals | None, call: ModelCall) -> None:
    if totals is not None:
        totals.input_tokens += call.input_tokens or 0
        totals.output_tokens += call.output_tokens or 0


@contextmanager
def model_call(role: str, model: str, inputs: dict[str, Any],
               span_type: str = CHAT) -> Iterator[ModelCall]:
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
    span = mlflow.start_span_no_context(name=f"model_call.{role}", span_type=span_type,
                                        parent_span=mlflow.get_current_active_span(),
                                        inputs=inputs,
                                        attributes={"mrag.role": role, "mrag.model": model})
    try:
        yield call
    except GeneratorExit:
        # The caller stopped reading a streamed answer early. Not an error
        span.end(outputs=call.output, attributes={"mrag.stopped_early": True})
        raise
    except BaseException as error:
        span.record_exception(error)
        span.end(outputs=call.output, status="ERROR")
        raise
    attributes: dict[str, Any] = {}
    if call.input_tokens is not None and call.output_tokens is not None:
        # MLflow's own token field, so the trace shows the total of all its model calls
        attributes[SpanAttributeKey.CHAT_USAGE] = {
            TokenUsageKey.INPUT_TOKENS: call.input_tokens,
            TokenUsageKey.OUTPUT_TOKENS: call.output_tokens,
            TokenUsageKey.TOTAL_TOKENS: call.input_tokens + call.output_tokens}
    span.end(outputs=call.output, attributes=attributes)
    add_tokens(totals, call)


def count_tool_call() -> None:
    if (totals := _current.get()) is not None:
        totals.tool_calls += 1


def set_fallback(name: str) -> None:
    # The backup path a request took, for example "single_answer" or "refusal"
    if (totals := _current.get()) is not None:
        totals.fallback = name


def git_tags() -> dict[str, str]:
    def git(*args: str) -> str:
        done = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True,
                              text=True, check=False)
        return done.stdout.strip()
    return {"git_commit": git("rev-parse", "HEAD") or "unknown",
            "git_dirty": "true" if git("status", "--porcelain") else "false"}


def config_params(profile: str) -> dict[str, str]:
    # Imported here because llm_client records its model calls through this module
    from mrag.llm_client import load_models

    params = {"profile": profile}
    # A short fingerprint of each config file shows which settings a run used
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        params[f"config.{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    entry = load_models().get(profile)
    for role, ref in (entry.models.items() if entry else []):
        params[f"model.{role}"] = f"{ref.name}@{ref.revision}" if ref.revision else ref.name
    return params


@contextmanager
def run(route: str, run_name: str | None = None,
        datasets: dict[str, str] | None = None) -> Iterator[str]:
    # One experiment run, for example an evaluation. Yields the run ID
    if not _enabled:
        raise TracingError("MLflow runs are only logged in the mac profile")
    with mlflow.start_run(experiment_id=experiment_id(route), run_name=run_name,
                          tags=git_tags()) as active:
        params = config_params(_profile)
        params.update({f"dataset.{name}": version for name, version in (datasets or {}).items()})
        mlflow.log_params(params)
        yield active.info.run_id


def log_results(metrics: dict[str, float], files: list[Path] | None = None) -> None:
    # Metrics and result files of the active run
    mlflow.log_metrics(metrics)
    for path in files or []:
        mlflow.log_artifact(str(path))
