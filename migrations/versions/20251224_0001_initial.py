"""initial

Revision ID: 20251224_0001
Revises: 
Create Date: 2025-12-24

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251224_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "note",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index(op.f("ix_note_title"), "note", ["title"], unique=False)
    op.create_index(op.f("ix_note_created_at"), "note", ["created_at"], unique=False)
    op.create_index(op.f("ix_note_updated_at"), "note", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_note_updated_at"), table_name="note")
    op.drop_index(op.f("ix_note_created_at"), table_name="note")
    op.drop_index(op.f("ix_note_title"), table_name="note")
    op.drop_table("note")
