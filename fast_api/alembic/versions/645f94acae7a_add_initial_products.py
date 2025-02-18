"""Add initial products

Revision ID: 645f94acae7a
Revises: ffd0a1b79516
Create Date: 2025-02-18 23:59:24.199395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '645f94acae7a'
down_revision: Union[str, None] = 'ffd0a1b79516'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
