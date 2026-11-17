# Shared test setup for the unit and the integration tests: a new app database for each test

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from mrag import config, db


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
