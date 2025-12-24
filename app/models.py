from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel, Field


class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=200)
    content: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
