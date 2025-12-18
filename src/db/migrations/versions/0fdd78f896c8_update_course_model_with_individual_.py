"""Update Course model with individual fields

Revision ID: 0fdd78f896c8
Revises: f7fd44497f51
Create Date: 2025-03-16 10:20:49.418499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0fdd78f896c8'
down_revision: Union[str, None] = 'f7fd44497f51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('courses', schema=None) as batch_op:
        # Add new columns
        batch_op.add_column(sa.Column('difficulty_level', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('target_age_group', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('estimated_time', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('points_reward', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('prerequisites', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.TIMESTAMP(), nullable=True))
        
        # Drop the course_metadata column if it exists
        # This is done in a separate try/except block because SQLite might not support
        # dropping columns in the same batch as adding columns
        try:
            batch_op.drop_column('course_metadata')
        except Exception as e:
            # If the column doesn't exist, just log and continue
            print(f"Note: Could not drop course_metadata column: {e}")


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('courses', schema=None) as batch_op:
        # Add back the course_metadata column
        batch_op.add_column(sa.Column('course_metadata', sa.JSON(), nullable=True))
        
        # Drop the new columns
        batch_op.drop_column('updated_at')
        batch_op.drop_column('tags')
        batch_op.drop_column('prerequisites')
        batch_op.drop_column('points_reward')
        batch_op.drop_column('estimated_time')
        batch_op.drop_column('target_age_group')
        batch_op.drop_column('difficulty_level')
