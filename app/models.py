from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, String
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(String(50), unique=True, index=True, nullable=False))
    password_hash: str
    is_superuser: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false", index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    title: str = Field(index=True, max_length=200)
    content: str = Field(default="")
    pinned: bool = Field(default=False, index=True)
    archived: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
