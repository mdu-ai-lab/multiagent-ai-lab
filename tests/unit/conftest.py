# Shared test setup: a temporary MLflow database, no server

import pytest

from mrag import tracing
from mrag.config import Settings


@pytest.fixture
def store(tmp_path, monkeypatch):
    # MLflow writes run files next to the working folder, so tests work in a temporary one
    monkeypatch.chdir(tmp_path)
    tracing.setup(Settings(profile="mac", mlflow_tracking_uri=f"sqlite:///{tmp_path}/mlflow.db"))
    yield tmp_path
    tracing.setup(Settings(profile="ci"))
