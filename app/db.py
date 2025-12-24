from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "notes.db"

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
