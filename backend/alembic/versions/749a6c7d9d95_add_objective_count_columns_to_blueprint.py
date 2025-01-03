"""Add objective count columns to Blueprint

Revision ID: 749a6c7d9d95
Revises: 005
Create Date: 2024-12-28 21:26:58.688562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '749a6c7d9d95'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('blueprints', 'status',
               existing_type=sa.VARCHAR(length=50),
               nullable=True,
               existing_server_default=sa.text("'draft'::character varying"))
    op.drop_index('idx_blueprints_created_by', table_name='blueprints')
    op.drop_index('idx_blueprints_topic_id', table_name='blueprints')
    op.drop_constraint('blueprints_topic_id_fkey', 'blueprints', type_='foreignkey')
    op.create_foreign_key(None, 'blueprints', 'topics', ['topic_id'], ['id'])
    op.drop_column('blueprints', 'parameters')
    op.alter_column('objectives', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
    op.alter_column('objectives', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
    op.drop_index('idx_topics_created_by', table_name='topics')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_topics_created_by', 'topics', ['created_by'], unique=False)
    op.alter_column('objectives', 'updated_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.alter_column('objectives', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.add_column('blueprints', sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'blueprints', type_='foreignkey')
    op.create_foreign_key('blueprints_topic_id_fkey', 'blueprints', 'topics', ['topic_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_blueprints_topic_id', 'blueprints', ['topic_id'], unique=False)
    op.create_index('idx_blueprints_created_by', 'blueprints', ['created_by'], unique=False)
    op.alter_column('blueprints', 'status',
               existing_type=sa.VARCHAR(length=50),
               nullable=False,
               existing_server_default=sa.text("'draft'::character varying"))
    # ### end Alembic commands ###
