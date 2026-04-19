"""add_user_profile_language_columns

Revision ID: 9f8e7d6c5b4a
Revises: 642a97bed49d
Create Date: 2026-04-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f8e7d6c5b4a"
down_revision: Union[str, None] = "642a97bed49d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column(
            "language_style",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "conversational_tone",
            sa.String(length=50),
            nullable=False,
            server_default="polite_formal",
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "relationship_start_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "relationship_start_date")
    op.drop_column("user_profiles", "conversational_tone")
    op.drop_column("user_profiles", "language_style")
