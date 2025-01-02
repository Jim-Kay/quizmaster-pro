"""add user settings

Revision ID: 003_add_user_settings
Revises: c73eb45ffe0e
Create Date: 2024-12-26 18:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_user_settings'
down_revision: Union[str, None] = 'c73eb45ffe0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create pgcrypto extension
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    
    # Create enum type for LLM provider
    op.execute("CREATE TYPE llm_provider_type AS ENUM ('openai', 'anthropic')")
    
    # Add new columns to users table
    op.add_column('users', sa.Column('llm_provider', postgresql.ENUM('openai', 'anthropic', name='llm_provider_type'), nullable=True))
    op.add_column('users', sa.Column('encrypted_openai_key', sa.String(), nullable=True))
    op.add_column('users', sa.Column('encrypted_anthropic_key', sa.String(), nullable=True))
    
    # Set default value for existing rows
    op.execute("UPDATE users SET llm_provider = 'openai' WHERE llm_provider IS NULL")
    
    # Make llm_provider non-nullable
    op.alter_column('users', 'llm_provider',
               existing_type=postgresql.ENUM('openai', 'anthropic', name='llm_provider_type'),
               nullable=False)


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'encrypted_anthropic_key')
    op.drop_column('users', 'encrypted_openai_key')
    op.drop_column('users', 'llm_provider')
    
    # Drop enum type
    op.execute('DROP TYPE llm_provider_type')
