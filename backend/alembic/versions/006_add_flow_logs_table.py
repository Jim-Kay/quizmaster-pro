"""add flow logs table

Revision ID: 006_add_flow_logs
Revises: 005_add_status_to_blueprints
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_add_flow_logs'
down_revision: Union[str, None] = '005_add_status_to_blueprints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create LogLevel enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE loglevel AS ENUM ('debug', 'info', 'warning', 'error');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create flow_logs table
    op.create_table('flow_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('level', sa.Enum('debug', 'info', 'warning', 'error', name='loglevel'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('log_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on execution_id for faster lookups
    op.create_index(op.f('ix_flow_logs_execution_id'), 'flow_logs', ['execution_id'], unique=False)

    # Create index on timestamp for faster sorting
    op.create_index(op.f('ix_flow_logs_timestamp'), 'flow_logs', ['timestamp'], unique=False)

    # Create index on level for filtering
    op.create_index(op.f('ix_flow_logs_level'), 'flow_logs', ['level'], unique=False)

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_flow_logs_level'), table_name='flow_logs')
    op.drop_index(op.f('ix_flow_logs_timestamp'), table_name='flow_logs')
    op.drop_index(op.f('ix_flow_logs_execution_id'), table_name='flow_logs')

    # Drop table
    op.drop_table('flow_logs')

    # Drop enum type if no other tables are using it
    op.execute("""
        DROP TYPE IF EXISTS loglevel;
    """)
