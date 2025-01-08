"""Initial schema

Revision ID: 20250107_initial_schema
Revises: 
Create Date: 2025-01-07 20:01:36.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250107_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create custom types
    op.execute("CREATE TYPE cognitivelevelenum AS ENUM ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')")
    op.execute("CREATE TYPE flowexecutionstatus AS ENUM ('pending', 'running', 'completed', 'failed')")
    op.execute("CREATE TYPE llm_provider_type AS ENUM ('openai', 'anthropic')")
    op.execute("CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic')")
    op.execute("CREATE TYPE loglevel AS ENUM ('debug', 'info', 'warning', 'error', 'critical')")

    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('llm_provider', sa.String(length=50), nullable=False),
        sa.Column('encrypted_openai_key', sa.String(length=255), nullable=True),
        sa.Column('encrypted_anthropic_key', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )

    # Create topics table
    op.create_table('topics',
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('topic_id')
    )

    # Create blueprints table
    op.create_table('blueprints',
        sa.Column('blueprint_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('content', postgresql.JSON(), nullable=True),
        sa.Column('output_folder', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('terminal_objectives_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('enabling_objectives_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.topic_id'], ),
        sa.PrimaryKeyConstraint('blueprint_id')
    )

    # Create terminal_objectives table
    op.create_table('terminal_objectives',
        sa.Column('terminal_objective_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('cognitive_level', sa.String(), nullable=False),
        sa.Column('topic_id', sa.UUID(), nullable=True),
        sa.Column('blueprint_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['blueprint_id'], ['blueprints.blueprint_id'], ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.topic_id'], ),
        sa.PrimaryKeyConstraint('terminal_objective_id')
    )

    # Create enabling_objectives table
    op.create_table('enabling_objectives',
        sa.Column('enabling_objective_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('number', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('cognitive_level', sa.String(), nullable=False),
        sa.Column('terminal_objective_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['terminal_objective_id'], ['terminal_objectives.terminal_objective_id'], ),
        sa.PrimaryKeyConstraint('enabling_objective_id')
    )

    # Create flow_executions table
    op.create_table('flow_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('flow_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('state', postgresql.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('log_file', sa.String(length=255), nullable=True),
        sa.Column('cache_key', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create flow_logs table
    op.create_table('flow_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('level', postgresql.ENUM('debug', 'info', 'warning', 'error', 'critical', name='loglevel'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('log_metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create idempotency_keys table
    op.create_table('idempotency_keys',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False, server_default=sa.text("(now() + '1 day'::interval)")),
        sa.ForeignKeyConstraint(['execution_id'], ['flow_executions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('key')
    )

def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_table('flow_logs')
    op.drop_table('flow_executions')
    op.drop_table('enabling_objectives')
    op.drop_table('terminal_objectives')
    op.drop_table('blueprints')
    op.drop_table('topics')
    op.drop_table('users')
    
    # Drop custom types
    op.execute('DROP TYPE loglevel')
    op.execute('DROP TYPE llmprovider')
    op.execute('DROP TYPE llm_provider_type')
    op.execute('DROP TYPE flowexecutionstatus')
    op.execute('DROP TYPE cognitivelevelenum')
