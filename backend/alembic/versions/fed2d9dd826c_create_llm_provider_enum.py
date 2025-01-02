"""create_llm_provider_enum

Revision ID: fed2d9dd826c
Revises: 003_add_user_settings
Create Date: 2024-12-26 18:58:23.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fed2d9dd826c'
down_revision: Union[str, None] = '003_add_user_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type if it doesn't exist
    op.execute("""
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'llmprovider') THEN
            CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic');
        END IF;
    END $$;
    """)

    # Update the column type
    op.execute("""
    ALTER TABLE users 
    ALTER COLUMN llm_provider TYPE llmprovider 
    USING llm_provider::text::llmprovider;
    """)


def downgrade() -> None:
    # Convert back to varchar
    op.execute("""
    ALTER TABLE users 
    ALTER COLUMN llm_provider TYPE varchar 
    USING llm_provider::text;
    """)
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS llmprovider;")
