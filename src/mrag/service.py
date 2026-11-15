# Core functions of the platform, shared by the API, the chat page, the demo and the tests.
# Questions go to the agent harness through harness.run() with the route table below.
# service.py never creates a model client or calls the search or a tool itself

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import version as package_version

from mrag import harness, tracing
from mrag.config import get_settings
from mrag.harness.context import Turn
from mrag.harness.loop import Events
from mrag.llm_client import load_models

log = logging.getLogger(__name__)


def chat_route(handle: harness.Harness) -> Iterator[str]:
    # Plain chat: the main model answers with the system prompt and the earlier turns
    return handle.answer()


# The routes a request can take. A router picks among them when there are more
ROUTES: dict[str, harness.Route] = {"chat": chat_route}


@dataclass(frozen=True)
class Health:
    status: str


@dataclass(frozen=True)
class VersionInfo:
    package: str
    profile: str
    git_commit: str
    git_dirty: bool
    pipeline_version: str


@dataclass(frozen=True)
class ModelInfo:
    role: str
    name: str
    source: str
    revision: str | None


@dataclass(frozen=True)
class ProfileModels:
    profile: str
    models: list[ModelInfo]


def start() -> None:
    # Called once when the API starts. Traces go to MLflow only while its server answers,
    # because the MLflow client retries for minutes when the server is down
    settings = get_settings()
    if tracing.setup(settings) and not tracing.server_reachable():
        tracing.setup(settings, trace=False)
        log.warning(
            "MLflow server not reachable at %s: requests are not traced",
            settings.mlflow_tracking_uri,
        )
    version()


def health() -> Health:
    return Health("ok")


@lru_cache
def version() -> VersionInfo:
    # Fixed at the first call: a running program keeps the code, configs and prompts it loaded
    profile = get_settings().profile
    parts = tracing.pipeline_parts(profile)
    return VersionInfo(
        package=package_version("multiagent-ai-lab"),
        profile=profile,
        git_commit=parts["git_commit"],
        git_dirty=parts["git_dirty"] == "true",
        pipeline_version=tracing.pipeline_version(parts),
    )


def models() -> ProfileModels:
    # Reads configs/models.yaml only. No model client is created
    profile = get_settings().profile
    entry = load_models().get(profile)
    found = entry.models.items() if entry else []
    return ProfileModels(
        profile,
        [ModelInfo(role, ref.name, ref.source or ref.name, ref.revision) for role, ref in found],
    )


def chat(message: str, history: list[Turn]) -> Events:
    return harness.run(harness.Request(message, history), ROUTES)
