from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load .env locally (harmless on PaaS)
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Import models so SQLModel metadata is populated
from sqlmodel import SQLModel  # noqa: E402
import app.models  # noqa: F401,E402


def _normalize_database_url(url: str) -> str:
    url = url.strip()

    # Some providers use postgres://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    # Ensure we use psycopg v3 driver
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]

    return url


database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL is not set. Alembic needs it to run migrations."
    )

config.set_main_option("sqlalchemy.url", _normalize_database_url(database_url))

# Target metadata for autogenerate
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
