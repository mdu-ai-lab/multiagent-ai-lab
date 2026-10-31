# Database layer: one SQLAlchemy engine and session factory for the app database.
# SQLite on the Mac now. PostgreSQL later only needs a different MRAG_DATABASE_URL.
# Tables are added later as classes based on Base. Alembic tracks every change.

from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mrag.config import get_settings


class Base(DeclarativeBase):
    pass


def _set_sqlite_pragmas(dbapi_connection, connection_record):
    # SQLite turns foreign keys off by default. WAL mode lets the API read
    # while the background worker writes
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


@lru_cache
def get_engine() -> Engine:
    url = make_url(get_settings().database_url)
    is_sqlite = url.get_backend_name() == "sqlite"

    # SQLite creates the file but not its folder
    if is_sqlite and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url)
    if is_sqlite:
        event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine())
