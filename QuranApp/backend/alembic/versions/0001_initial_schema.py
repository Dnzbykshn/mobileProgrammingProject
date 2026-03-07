"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-28

Tables created via SQLAlchemy create_all() — this migration is a no-op marker
so Alembic tracks changes from this point forward.
"""
from typing import Sequence, Union

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass  # Tables already created by SQLAlchemy create_all()


def downgrade() -> None:
    pass
