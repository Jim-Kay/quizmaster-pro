"""Add objective count columns

Revision ID: 873a3396bead
Revises: 749a6c7d9d95
Create Date: 2024-12-28 21:32:50.416995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '873a3396bead'
down_revision: Union[str, None] = '749a6c7d9d95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blueprints', sa.Column('terminal_objectives_count', sa.Integer(), nullable=True))
    op.add_column('blueprints', sa.Column('enabling_objectives_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('blueprints', 'enabling_objectives_count')
    op.drop_column('blueprints', 'terminal_objectives_count')
    # ### end Alembic commands ###
