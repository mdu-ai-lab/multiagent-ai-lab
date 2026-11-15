# Shared test setup: a temporary MLflow database with no server and a new app database

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from mrag import config, db, tracing
from mrag.config import Settings


@pytest.fixture
def store(tmp_path, monkeypatch):
    # MLflow writes run files next to the working folder, so tests work in a temporary one
    monkeypatch.chdir(tmp_path)
    tracing.setup(Settings(profile="mac", mlflow_tracking_uri=f"sqlite:///{tmp_path}/mlflow.db"))
    yield tmp_path
    tracing.setup(Settings(profile="ci"))


def alembic_config() -> Config:
    return Config(toml_file=config.PROJECT_ROOT / "pyproject.toml")


def clear_caches() -> None:
    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()


@pytest.fixture
def database(tmp_path, monkeypatch) -> Iterator[Config]:
    # A new SQLite file built by the migrations, as on a new machine
    monkeypatch.setenv("MRAG_DATABASE_URL", f"sqlite:///{tmp_path / 'app.db'}")
    clear_caches()
    alembic = alembic_config()
    command.upgrade(alembic, "head")
    yield alembic
    db.get_engine().dispose()
    clear_caches()


@pytest.fixture
def session(database) -> Iterator[Session]:
    with db.get_sessionmaker()() as s:
        yield s
