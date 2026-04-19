"""add_pathway_definition_tables

Revision ID: a8b7c6d5e4f3
Revises: f1c2d3e4a5b6
Create Date: 2026-04-17 00:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a8b7c6d5e4f3"
down_revision: Union[str, None] = "f1c2d3e4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pathway_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("pathway_type", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("total_days", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pathway_definitions_slug"), "pathway_definitions", ["slug"], unique=True)

    op.create_table(
        "pathway_definition_days",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("definition_id", sa.UUID(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_day0", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_skippable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("definition_id", "day_number", name="uq_pathway_definition_days_definition_day"),
    )
    op.create_index(op.f("ix_pathway_definition_days_definition_id"), "pathway_definition_days", ["definition_id"], unique=False)

    op.create_table(
        "pathway_definition_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("definition_day_id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("task_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("definition_day_id", "order_index", name="uq_pathway_definition_tasks_day_order"),
    )
    op.create_index(op.f("ix_pathway_definition_tasks_definition_day_id"), "pathway_definition_tasks", ["definition_day_id"], unique=False)

    op.create_foreign_key(
        "pathway_definition_days_definition_id_fkey",
        "pathway_definition_days",
        "pathway_definitions",
        ["definition_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "pathway_definition_tasks_definition_day_id_fkey",
        "pathway_definition_tasks",
        "pathway_definition_days",
        ["definition_day_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("pathway_definition_tasks_definition_day_id_fkey", "pathway_definition_tasks", type_="foreignkey")
    op.drop_constraint("pathway_definition_days_definition_id_fkey", "pathway_definition_days", type_="foreignkey")

    op.drop_index(op.f("ix_pathway_definition_tasks_definition_day_id"), table_name="pathway_definition_tasks")
    op.drop_table("pathway_definition_tasks")

    op.drop_index(op.f("ix_pathway_definition_days_definition_id"), table_name="pathway_definition_days")
    op.drop_table("pathway_definition_days")

    op.drop_index(op.f("ix_pathway_definitions_slug"), table_name="pathway_definitions")
    op.drop_table("pathway_definitions")
