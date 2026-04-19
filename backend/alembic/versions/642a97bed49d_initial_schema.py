"""initial_schema

Revision ID: 642a97bed49d
Revises:
Create Date: 2026-02-28 17:29:08.056440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "642a97bed49d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("emotion_category", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("phase", sa.String(length=20), server_default="IDLE", nullable=True),
        sa.Column("gathering_context", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("prescription_id", sa.UUID(), nullable=True),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("emotion_category", sa.String(length=50), nullable=True),
        sa.Column("prescription_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "daily_plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("prescription_id", sa.UUID(), nullable=True),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("journey_title", sa.String(length=255), nullable=True),
        sa.Column("journey_type", sa.String(length=50), nullable=True),
        sa.Column("topic_summary", sa.Text(), nullable=True),
        sa.Column("topic_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("total_days", sa.Integer(), nullable=True),
        sa.Column("current_day", sa.Integer(), nullable=True),
        sa.Column("day0_skipped", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("sender", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "plan_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("task_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("task_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.String(length=128), server_default="unknown", nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_token_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_device_id"), "refresh_tokens", ["device_id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_revoked_at"), "refresh_tokens", ["revoked_at"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("known_topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("personality_notes", sa.Text(), nullable=True),
        sa.Column("interaction_count", sa.Integer(), nullable=True),
        sa.Column("last_mood", sa.String(length=50), nullable=True),
        sa.Column("preferred_tone", sa.String(length=20), nullable=True),
        sa.Column("spiritual_preferences", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("behavioral_insights", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("memory_summary", sa.Text(), nullable=True),
        sa.Column("last_memory_summary_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_profiles_user_id"), "user_profiles", ["user_id"], unique=True)

    op.create_table(
        "knowledge_units",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("metadata_idx", "knowledge_units", ["metadata"], unique=False, postgresql_using="gin")
    op.create_index("knowledge_vec_idx", "knowledge_units", ["embedding"], unique=False, postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"})

    op.create_table(
        "user_memories",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("memory_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("importance_score", sa.Integer(), server_default="50", nullable=True),
        sa.Column("access_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conversation_id", sa.UUID(), nullable=True),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_memories_embedding", "user_memories", ["embedding"], unique=False, postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"})
    op.create_index("idx_user_memories_importance", "user_memories", [sa.text("importance_score DESC")], unique=False, postgresql_where=sa.text("is_deleted = false"))
    op.create_index("idx_user_memories_user_type", "user_memories", ["user_id", "memory_type"], unique=False, postgresql_where=sa.text("is_deleted = false"))
    op.create_index(op.f("ix_user_memories_memory_type"), "user_memories", ["memory_type"], unique=False)
    op.create_index(op.f("ix_user_memories_user_id"), "user_memories", ["user_id"], unique=False)

    op.create_table(
        "esma_ul_husna",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("appellation", sa.String(length=100), nullable=True),
        sa.Column("meaning", sa.Text(), nullable=True),
        sa.Column("psychological_benefits", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("referral_note", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("esma_embedding_idx", "esma_ul_husna", ["embedding"], unique=False, postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"})

    op.create_table(
        "prophet_duas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("arabic_text", sa.Text(), nullable=True),
        sa.Column("turkish_text", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("emotional_tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("dua_embedding_idx", "prophet_duas", ["embedding"], unique=False, postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"})

    op.create_table(
        "prayer_districts",
        sa.Column("district_id", sa.String(length=20), nullable=False),
        sa.Column("district_name", sa.String(length=100), nullable=False),
        sa.Column("state_id", sa.String(length=20), nullable=False),
        sa.Column("state_name", sa.String(length=100), nullable=False),
        sa.Column("country_id", sa.String(length=20), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("district_id"),
    )
    op.create_index("ix_prayer_districts_country", "prayer_districts", ["country_id"], unique=False)
    op.create_index("ix_prayer_districts_state", "prayer_districts", ["state_id"], unique=False)

    op.create_table(
        "prayer_times",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("district_id", sa.String(length=20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("imsak", sa.String(length=5), nullable=False),
        sa.Column("gunes", sa.String(length=5), nullable=False),
        sa.Column("ogle", sa.String(length=5), nullable=False),
        sa.Column("ikindi", sa.String(length=5), nullable=False),
        sa.Column("aksam", sa.String(length=5), nullable=False),
        sa.Column("yatsi", sa.String(length=5), nullable=False),
        sa.Column("hijri_day", sa.SmallInteger(), nullable=True),
        sa.Column("hijri_month", sa.SmallInteger(), nullable=True),
        sa.Column("hijri_month_name", sa.String(length=30), nullable=True),
        sa.Column("hijri_year", sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prayer_times_district_date", "prayer_times", ["district_id", "date"], unique=True)

    op.create_table(
        "keyword_canonical_map",
        sa.Column("raw_keyword", sa.Text(), nullable=False),
        sa.Column("canonical_keyword", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("raw_keyword"),
    )
    op.create_index("idx_keyword_canonical_map_canonical", "keyword_canonical_map", ["canonical_keyword"], unique=False)

    op.create_table(
        "knowledge_units_graph_keywords",
        sa.Column("knowledge_unit_id", sa.Integer(), nullable=False),
        sa.Column("canonical_keyword", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("knowledge_unit_id", "canonical_keyword"),
    )
    op.create_index("idx_knowledge_units_graph_keywords_keyword", "knowledge_units_graph_keywords", ["canonical_keyword"], unique=False)

    op.create_table(
        "keyword_taxonomy_map",
        sa.Column("canonical_keyword", sa.Text(), nullable=False),
        sa.Column("root_category", sa.Text(), nullable=False),
        sa.Column("sub_category", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.PrimaryKeyConstraint("canonical_keyword"),
    )
    op.create_index("idx_taxonomy_root", "keyword_taxonomy_map", ["root_category"], unique=False)
    op.create_index("idx_taxonomy_sub", "keyword_taxonomy_map", ["sub_category"], unique=False)

    op.create_foreign_key("conversations_user_id_fkey", "conversations", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("conversations_prescription_id_fkey", "conversations", "prescriptions", ["prescription_id"], ["id"])
    op.create_foreign_key("conversations_plan_id_fkey", "conversations", "daily_plans", ["plan_id"], ["id"])
    op.create_foreign_key("prescriptions_user_id_fkey", "prescriptions", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("prescriptions_conversation_id_fkey", "prescriptions", "conversations", ["conversation_id"], ["id"])
    op.create_foreign_key("daily_plans_user_id_fkey", "daily_plans", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("daily_plans_prescription_id_fkey", "daily_plans", "prescriptions", ["prescription_id"], ["id"])
    op.create_foreign_key("daily_plans_conversation_id_fkey", "daily_plans", "conversations", ["conversation_id"], ["id"])
    op.create_foreign_key("messages_conversation_id_fkey", "messages", "conversations", ["conversation_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("plan_tasks_plan_id_fkey", "plan_tasks", "daily_plans", ["plan_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("refresh_tokens_user_id_fkey", "refresh_tokens", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("user_profiles_user_id_fkey", "user_profiles", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("user_memories_user_id_fkey", "user_memories", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("user_memories_conversation_id_fkey", "user_memories", "conversations", ["conversation_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("user_memories_plan_id_fkey", "user_memories", "daily_plans", ["plan_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("knowledge_units_graph_keywords_knowledge_unit_id_fkey", "knowledge_units_graph_keywords", "knowledge_units", ["knowledge_unit_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("knowledge_units_graph_keywords_knowledge_unit_id_fkey", "knowledge_units_graph_keywords", type_="foreignkey")
    op.drop_constraint("user_memories_plan_id_fkey", "user_memories", type_="foreignkey")
    op.drop_constraint("user_memories_conversation_id_fkey", "user_memories", type_="foreignkey")
    op.drop_constraint("user_memories_user_id_fkey", "user_memories", type_="foreignkey")
    op.drop_constraint("user_profiles_user_id_fkey", "user_profiles", type_="foreignkey")
    op.drop_constraint("refresh_tokens_user_id_fkey", "refresh_tokens", type_="foreignkey")
    op.drop_constraint("plan_tasks_plan_id_fkey", "plan_tasks", type_="foreignkey")
    op.drop_constraint("messages_conversation_id_fkey", "messages", type_="foreignkey")
    op.drop_constraint("daily_plans_conversation_id_fkey", "daily_plans", type_="foreignkey")
    op.drop_constraint("daily_plans_prescription_id_fkey", "daily_plans", type_="foreignkey")
    op.drop_constraint("daily_plans_user_id_fkey", "daily_plans", type_="foreignkey")
    op.drop_constraint("prescriptions_conversation_id_fkey", "prescriptions", type_="foreignkey")
    op.drop_constraint("prescriptions_user_id_fkey", "prescriptions", type_="foreignkey")
    op.drop_constraint("conversations_plan_id_fkey", "conversations", type_="foreignkey")
    op.drop_constraint("conversations_prescription_id_fkey", "conversations", type_="foreignkey")
    op.drop_constraint("conversations_user_id_fkey", "conversations", type_="foreignkey")

    op.drop_table("keyword_taxonomy_map")
    op.drop_table("knowledge_units_graph_keywords")
    op.drop_table("keyword_canonical_map")
    op.drop_table("prayer_times")
    op.drop_table("prayer_districts")
    op.drop_table("prophet_duas")
    op.drop_table("esma_ul_husna")
    op.drop_table("user_memories")
    op.drop_table("knowledge_units")
    op.drop_table("user_profiles")
    op.drop_table("refresh_tokens")
    op.drop_table("plan_tasks")
    op.drop_table("messages")
    op.drop_table("daily_plans")
    op.drop_table("prescriptions")
    op.drop_table("conversations")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
