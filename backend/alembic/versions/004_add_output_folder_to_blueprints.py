"""add output_folder to blueprints

Revision ID: 004
Revises: 77b4b1a35f6a
Create Date: 2024-12-28 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '77b4b1a35f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add output_folder column to blueprints table
    op.add_column('blueprints', sa.Column('output_folder', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove output_folder column from blueprints table
    op.drop_column('blueprints', 'output_folder')
