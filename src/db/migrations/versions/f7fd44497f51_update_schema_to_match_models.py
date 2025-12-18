"""update_schema_to_match_models

Revision ID: f7fd44497f51
Revises: f0077e8d4b64
Create Date: 2025-03-15 21:50:43.004566

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7fd44497f51'
down_revision: Union[str, None] = 'f0077e8d4b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column to courses table
    op.add_column('courses', sa.Column('updated_at', sa.TIMESTAMP(), nullable=True))
    
    # Update existing rows to set updated_at to the same value as created_at
    op.execute("UPDATE courses SET updated_at = created_at")
    
    # Remove course_metadata column from courses table
    op.drop_column('courses', 'course_metadata')
    
    # Update enum values for topic column in courses table
    # First, create a temporary table with the new schema
    op.execute("""
    CREATE TABLE courses_new (
        id TEXT PRIMARY KEY,
        topic VARCHAR(11) NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    
    # Copy data from old table to new table, converting enum values
    op.execute("""
    INSERT INTO courses_new (id, topic, name, description, created_at, updated_at)
    SELECT id, 
           CASE 
               WHEN topic = 'Informatics' THEN 'informatics'
               WHEN topic = 'Math' THEN 'mathematics'
               ELSE topic
           END,
           name, description, created_at, updated_at
    FROM courses
    """)
    
    # Drop old table and rename new table
    op.execute("DROP TABLE courses")
    op.execute("ALTER TABLE courses_new RENAME TO courses")
    
    # Create indexes on the new table
    op.execute("CREATE INDEX idx_course_topic ON courses (topic)")
    op.execute("CREATE INDEX idx_course_name ON courses (name)")


def downgrade() -> None:
    # Add course_metadata column back to courses table
    op.add_column('courses', sa.Column('course_metadata', sa.JSON(), nullable=True))
    
    # Update enum values for topic column in courses table back to original values
    # First, create a temporary table with the old schema
    op.execute("""
    CREATE TABLE courses_old (
        id TEXT PRIMARY KEY,
        topic VARCHAR(11) NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        course_metadata JSON,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    
    # Copy data from new table to old table, converting enum values back
    op.execute("""
    INSERT INTO courses_old (id, topic, name, description, created_at, updated_at)
    SELECT id, 
           CASE 
               WHEN topic = 'informatics' THEN 'Informatics'
               WHEN topic = 'mathematics' THEN 'Math'
               ELSE topic
           END,
           name, description, created_at, updated_at
    FROM courses
    """)
    
    # Drop new table and rename old table
    op.execute("DROP TABLE courses")
    op.execute("ALTER TABLE courses_old RENAME TO courses")
    
    # Create indexes on the old table
    op.execute("CREATE INDEX idx_course_topic ON courses (topic)")
    op.execute("CREATE INDEX idx_course_name ON courses (name)")
    
    # Remove updated_at column from courses table
    op.drop_column('courses', 'updated_at')
