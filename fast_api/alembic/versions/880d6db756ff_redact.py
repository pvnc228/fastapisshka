"""redact

Revision ID: 880d6db756ff
Revises: 645f94acae7a
Create Date: 2025-02-19 00:08:00.298309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models import Product


# revision identifiers, used by Alembic.
revision: str = '880d6db756ff'
down_revision: Union[str, None] = '645f94acae7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    

    # Добавляем тестовые данные
    op.bulk_insert(
        Product.__table__,
        [
            {
                "name": "КАСКО Премиум",
                "category": "Автострахование",
                "description": "Полная защита автомобиля от всех рисков",
                "price": 25000,
                "insurance_type": "КАСКО"
            },
            {
                "name": "ОСАГО Базовый",
                "category": "Автострахование",
                "description": "Обязательное страхование автогражданской ответственности",
                "price": 5000,
                "insurance_type": "ОСАГО"
            },
            {
                "name": "Защита дома",
                "category": "Имущество",
                "description": "Страхование недвижимости от пожаров и стихийных бедствий",
                "price": 15000,
                "insurance_type": "Имущество"
            }
        ]
    )

def downgrade():
    op.drop_table('products')