"""rename topic user_id to created_by

Revision ID: 007_rename_topic_user_id
Revises: 006_add_flow_logs
Create Date: 2024-03-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007_rename_topic_user_id'
down_revision: Union[str, None] = '006_add_flow_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('topics_user_id_fkey', 'topics', type_='foreignkey')
    
    # Rename the column
    op.alter_column('topics', 'user_id', new_column_name='created_by')
    
    # Add back the foreign key constraint with the new column name
    op.create_foreign_key(
        'topics_created_by_fkey',
        'topics',
        'users',
        ['created_by'],
        ['user_id']
    )

def downgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('topics_created_by_fkey', 'topics', type_='foreignkey')
    
    # Rename the column back
    op.alter_column('topics', 'created_by', new_column_name='user_id')
    
    # Add back the original foreign key constraint
    op.create_foreign_key(
        'topics_user_id_fkey',
        'topics',
        'users',
        ['user_id'],
        ['user_id']
    )
