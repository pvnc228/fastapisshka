"""add_role_field_and_admin_user

Revision ID: a46a4ba47045
Revises: 8cbc1fbbe1d0
Create Date: 2025-03-23 14:24:31.125683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models import User
from utils import hash_password


# revision identifiers, used by Alembic.
revision: str = 'a46a4ba47045'
down_revision: Union[str, None] = '8cbc1fbbe1d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))
    op.bulk_insert(
        User.__table__,
        [
            {
                'email': 'admin@admin.org',
                'hashed_password': hash_password('1111'),
                'role': 'admin'
            }
        ]
    )


def downgrade() -> None:
    # Удаляем администратора
    op.execute("DELETE FROM users WHERE email = 'admin@admin.org'")

    # Удаляем поле role
    op.drop_column('users', 'role')
