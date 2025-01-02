"""add status to blueprints

Revision ID: 005
Revises: 004
Create Date: 2024-12-28 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status column to blueprints table with default value 'draft'
    op.add_column('blueprints', sa.Column('status', sa.String(50), nullable=False, server_default='draft'))
    
    # Make description and content nullable
    op.alter_column('blueprints', 'description',
                    existing_type=sa.Text(),
                    nullable=True)
    
    # Add content column if it doesn't exist
    op.add_column('blueprints', sa.Column('content', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove status column from blueprints table
    op.drop_column('blueprints', 'status')
    
    # Make description non-nullable again
    op.alter_column('blueprints', 'description',
                    existing_type=sa.Text(),
                    nullable=False)
    
    # Remove content column
    op.drop_column('blueprints', 'content')
