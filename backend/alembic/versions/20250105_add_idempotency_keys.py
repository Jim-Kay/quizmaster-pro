"""add idempotency keys

Revision ID: 20250105_add_idempotency_keys
Revises: 20250104_add_flow_logs
Create Date: 2025-01-05 17:49:18.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20250105_add_idempotency_keys'
down_revision = '20250104_add_flow_logs'  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('execution_id', UUID(as_uuid=True), sa.ForeignKey('flow_executions.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    
    op.create_index('idx_idempotency_keys_user_id', 'idempotency_keys', ['user_id'])
    op.create_index('idx_idempotency_keys_created_at', 'idempotency_keys', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_idempotency_keys_created_at')
    op.drop_index('idx_idempotency_keys_user_id')
    op.drop_table('idempotency_keys')
