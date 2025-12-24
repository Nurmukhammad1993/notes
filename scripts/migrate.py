from __future__ import annotations

import os

from alembic import command
from alembic.config import Config

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _normalize_database_url(url: str) -> str:
    url = url.strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]

    return url


def run() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", _normalize_database_url(database_url))

    try:
        command.upgrade(cfg, "head")
        return
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        duplicate_markers = [
            "already exists",
            "DuplicateTable",
            "duplicate table",
            "relation \"note\" already exists",
        ]

        if any(marker in message for marker in duplicate_markers):
            # Baseline an existing schema (created earlier without Alembic)
            command.stamp(cfg, "head")
            command.upgrade(cfg, "head")
            return

        raise


if __name__ == "__main__":
    run()
