"""remove_prescription_tables_and_columns

Revision ID: d4e5f6a7b8c9
Revises: a8b7c6d5e4f3
Create Date: 2026-04-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'a8b7c6d5e4f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('pathways_prescription_id_fkey', 'pathways', type_='foreignkey')
    op.drop_column('pathways', 'prescription_id')

    op.drop_constraint('conversations_prescription_id_fkey', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'prescription_id')

    op.drop_table('prescriptions')


def downgrade() -> None:
    op.create_table(
        'prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('emotion_category', sa.String(50), nullable=True),
        sa.Column('prescription_data', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('conversations', sa.Column('prescription_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('conversations_prescription_id_fkey', 'conversations', 'prescriptions', ['prescription_id'], ['id'])

    op.add_column('pathways', sa.Column('prescription_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('pathways_prescription_id_fkey', 'pathways', 'prescriptions', ['prescription_id'], ['id'])
