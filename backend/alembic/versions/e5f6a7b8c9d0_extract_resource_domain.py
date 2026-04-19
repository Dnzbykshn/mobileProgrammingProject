"""extract_resource_domain

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-17 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "knowledge_units_graph_keywords_knowledge_unit_id_fkey",
        "knowledge_units_graph_keywords",
        type_="foreignkey",
    )

    op.drop_table("keyword_taxonomy_map")
    op.drop_table("knowledge_units_graph_keywords")
    op.drop_table("keyword_canonical_map")
    op.drop_table("prophet_duas")
    op.drop_table("esma_ul_husna")
    op.drop_table("knowledge_units")


def downgrade() -> None:
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
    op.create_index(
        "metadata_idx",
        "knowledge_units",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "knowledge_vec_idx",
        "knowledge_units",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

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
    op.create_index(
        "esma_embedding_idx",
        "esma_ul_husna",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

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
    op.create_index(
        "dua_embedding_idx",
        "prophet_duas",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "keyword_canonical_map",
        sa.Column("raw_keyword", sa.Text(), nullable=False),
        sa.Column("canonical_keyword", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("raw_keyword"),
    )
    op.create_index(
        "idx_keyword_canonical_map_canonical",
        "keyword_canonical_map",
        ["canonical_keyword"],
        unique=False,
    )

    op.create_table(
        "knowledge_units_graph_keywords",
        sa.Column("knowledge_unit_id", sa.Integer(), nullable=False),
        sa.Column("canonical_keyword", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("knowledge_unit_id", "canonical_keyword"),
    )
    op.create_index(
        "idx_knowledge_units_graph_keywords_keyword",
        "knowledge_units_graph_keywords",
        ["canonical_keyword"],
        unique=False,
    )

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

    op.create_foreign_key(
        "knowledge_units_graph_keywords_knowledge_unit_id_fkey",
        "knowledge_units_graph_keywords",
        "knowledge_units",
        ["knowledge_unit_id"],
        ["id"],
        ondelete="CASCADE",
    )
