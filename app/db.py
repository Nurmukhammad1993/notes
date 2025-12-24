from __future__ import annotations

import os

from sqlmodel import SQLModel, Session, create_engine

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

def _normalize_database_url(url: str) -> str:
    url = url.strip()

    # Some providers (and older guides) use postgres:// which SQLAlchemy treats as postgresql.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    # Ensure SQLAlchemy uses psycopg v3 driver when provider gives plain postgresql://...
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]

    return url


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. This app is configured to run with Postgres only. "
        "Example: postgresql+psycopg://notes:notespass@localhost:5433/notes"
    )

engine = create_engine(_normalize_database_url(DATABASE_URL), pool_pre_ping=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
