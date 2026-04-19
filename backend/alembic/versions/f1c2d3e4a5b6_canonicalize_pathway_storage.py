"""canonicalize_pathway_storage

Revision ID: f1c2d3e4a5b6
Revises: c3a7d9e2f4b1
Create Date: 2026-04-16 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1c2d3e4a5b6"
down_revision: Union[str, None] = "c3a7d9e2f4b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop foreign keys with legacy names before table/column renames.
    op.drop_constraint("conversations_plan_id_fkey", "conversations", type_="foreignkey")
    op.drop_constraint("plan_tasks_plan_id_fkey", "plan_tasks", type_="foreignkey")
    op.drop_constraint("user_memories_plan_id_fkey", "user_memories", type_="foreignkey")
    op.drop_constraint("daily_plans_user_id_fkey", "daily_plans", type_="foreignkey")
    op.drop_constraint("daily_plans_prescription_id_fkey", "daily_plans", type_="foreignkey")
    op.drop_constraint("daily_plans_conversation_id_fkey", "daily_plans", type_="foreignkey")

    # Rename columns first.
    op.alter_column("conversations", "plan_id", new_column_name="pathway_id")
    op.alter_column("user_memories", "plan_id", new_column_name="pathway_id")
    op.alter_column("plan_tasks", "plan_id", new_column_name="pathway_id")
    op.alter_column("daily_plans", "journey_title", new_column_name="title")
    op.alter_column("daily_plans", "journey_type", new_column_name="pathway_type")

    # Rename tables.
    op.rename_table("daily_plans", "pathways")
    op.rename_table("plan_tasks", "pathway_tasks")

    # Recreate foreign keys with canonical names.
    op.create_foreign_key(
        "pathways_user_id_fkey",
        "pathways",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "pathways_prescription_id_fkey",
        "pathways",
        "prescriptions",
        ["prescription_id"],
        ["id"],
    )
    op.create_foreign_key(
        "pathways_conversation_id_fkey",
        "pathways",
        "conversations",
        ["conversation_id"],
        ["id"],
    )
    op.create_foreign_key(
        "conversations_pathway_id_fkey",
        "conversations",
        "pathways",
        ["pathway_id"],
        ["id"],
    )
    op.create_foreign_key(
        "pathway_tasks_pathway_id_fkey",
        "pathway_tasks",
        "pathways",
        ["pathway_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "user_memories_pathway_id_fkey",
        "user_memories",
        "pathways",
        ["pathway_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop canonical FKs.
    op.drop_constraint("user_memories_pathway_id_fkey", "user_memories", type_="foreignkey")
    op.drop_constraint("pathway_tasks_pathway_id_fkey", "pathway_tasks", type_="foreignkey")
    op.drop_constraint("conversations_pathway_id_fkey", "conversations", type_="foreignkey")
    op.drop_constraint("pathways_conversation_id_fkey", "pathways", type_="foreignkey")
    op.drop_constraint("pathways_prescription_id_fkey", "pathways", type_="foreignkey")
    op.drop_constraint("pathways_user_id_fkey", "pathways", type_="foreignkey")

    # Rename tables back.
    op.rename_table("pathway_tasks", "plan_tasks")
    op.rename_table("pathways", "daily_plans")

    # Rename columns back.
    op.alter_column("daily_plans", "pathway_type", new_column_name="journey_type")
    op.alter_column("daily_plans", "title", new_column_name="journey_title")
    op.alter_column("plan_tasks", "pathway_id", new_column_name="plan_id")
    op.alter_column("user_memories", "pathway_id", new_column_name="plan_id")
    op.alter_column("conversations", "pathway_id", new_column_name="plan_id")

    # Recreate legacy FKs.
    op.create_foreign_key(
        "daily_plans_user_id_fkey",
        "daily_plans",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "daily_plans_prescription_id_fkey",
        "daily_plans",
        "prescriptions",
        ["prescription_id"],
        ["id"],
    )
    op.create_foreign_key(
        "daily_plans_conversation_id_fkey",
        "daily_plans",
        "conversations",
        ["conversation_id"],
        ["id"],
    )
    op.create_foreign_key(
        "conversations_plan_id_fkey",
        "conversations",
        "daily_plans",
        ["plan_id"],
        ["id"],
    )
    op.create_foreign_key(
        "plan_tasks_plan_id_fkey",
        "plan_tasks",
        "daily_plans",
        ["plan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "user_memories_plan_id_fkey",
        "user_memories",
        "daily_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )
