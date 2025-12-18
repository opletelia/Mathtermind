"""Merge heads

Revision ID: 7fedef395e59
Revises: 0fdd78f896c8, 25108061be61
Create Date: 2025-03-16 10:21:34.800202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fedef395e59'
down_revision: Union[str, None] = ('0fdd78f896c8', '25108061be61')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
