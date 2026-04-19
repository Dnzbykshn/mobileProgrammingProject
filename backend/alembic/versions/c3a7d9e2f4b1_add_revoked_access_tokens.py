"""add_revoked_access_tokens

Revision ID: c3a7d9e2f4b1
Revises: 9f8e7d6c5b4a
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3a7d9e2f4b1"
down_revision: Union[str, None] = "9f8e7d6c5b4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revoked_access_tokens",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(op.f("ix_revoked_access_tokens_expires_at"), "revoked_access_tokens", ["expires_at"], unique=False)
    op.create_index(op.f("ix_revoked_access_tokens_user_id"), "revoked_access_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_revoked_access_tokens_user_id"), table_name="revoked_access_tokens")
    op.drop_index(op.f("ix_revoked_access_tokens_expires_at"), table_name="revoked_access_tokens")
    op.drop_table("revoked_access_tokens")
