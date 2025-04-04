"""Add author

Revision ID: 8cbc1fbbe1d0
Revises: 9e2be42d5d8c
Create Date: 2025-03-21 22:10:05.586234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cbc1fbbe1d0'
down_revision: Union[str, None] = '9e2be42d5d8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reviews', sa.Column('author', sa.Text(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reviews', 'author')
    # ### end Alembic commands ###
