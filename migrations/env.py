# Alembic migration environment.
# The database URL and the table list come from mrag, so there is one source of settings.

import logging

from alembic import context

from mrag.config import get_settings
from mrag.db import Base, get_engine

# Show Alembic's progress lines ("Running upgrade ...") without an alembic.ini file
logging.basicConfig(format="%(levelname)-5.5s [%(name)s] %(message)s")
logging.getLogger("alembic").setLevel(logging.INFO)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # Writes SQL to the screen instead of running it (alembic upgrade head --sql)
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite can't change most columns in place. Batch mode copies the table instead
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
