"""Add new fields to Product model

Revision ID: 19e6fa038ec8
Revises: 880d6db756ff
Create Date: 2025-02-19 00:36:16.138874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models import Product


# revision identifiers, used by Alembic.
revision: str = '19e6fa038ec8'
down_revision: Union[str, None] = '880d6db756ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # Добавляем новые поля (если они еще не добавлены)
  

    # Заполняем данные для всех продуктов
    op.bulk_insert(
        Product.__table__,
        [
            {
                "name": "КАСКО Классика",
                "category": "Автострахование",
                "description": "Классический пакет страхования автомобиля",
                "price": 0,  # Стоимость расчётная
                "insurance_type": "КАСКО",
                "max_car_age": 20,
                "insurance_amount": 0,  # Равна стоимости авто
                "insurance_duration": "12 мес.",
                "policy_cost": 0,  # Расчётная
                "risks": "Ущерб, Полная гибель, Хищение, угон",
                "payment_conditions": "рассрочка в 2 платежа",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": True,
                "compensation_form": "Ремонт на СТОА или выплата деньгами",
                "payout_without_certificates": False
            },
            {
                "name": "Практичное КАСКО",
                "category": "Автострахование",
                "description": "Базовый пакет страхования автомобиля",
                "price": 2050,
                "insurance_type": "КАСКО",
                "max_car_age": 20,
                "insurance_amount": 400000,
                "insurance_duration": "12 мес.",
                "policy_cost": 2050,
                "risks": "Ущерб, Полная гибель",
                "payment_conditions": "единовременно",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": True,
                "compensation_form": "Ремонт на СТОА или выплата деньгами",
                "payout_without_certificates": False
            },
            {
                "name": "КАСКО Профи",
                "category": "Автострахование",
                "description": "Расширенный пакет страхования автомобиля",
                "price": 0,  # Стоимость расчётная
                "insurance_type": "КАСКО",
                "max_car_age": 10,
                "insurance_amount": 0,  # Равна стоимости авто
                "insurance_duration": "12 мес.",
                "policy_cost": 0,  # Расчётная
                "risks": "Ущерб, Полная гибель, Хищение, угон",
                "payment_conditions": "единовременно",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": True,
                "compensation_form": "Ремонт на СТОА или выплата деньгами",
                "payout_without_certificates": True
            },
            {
                "name": "КАСКО Пополам",
                "category": "Автострахование",
                "description": "Пакет страхования с разделением затрат",
                "price": 0,  # Стоимость расчётная
                "insurance_type": "КАСКО",
                "max_car_age": 10,
                "insurance_amount": 0,  # Равна стоимости авто
                "insurance_duration": "12 мес.",
                "policy_cost": 0,  # Расчётная
                "risks": "Ущерб, Полная гибель, Хищение, угон",
                "payment_conditions": "единовременно",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": True,
                "compensation_form": "Ремонт на СТОА или выплата деньгами",
                "payout_without_certificates": True
            },
            {
                "name": "Всё под контролем",
                "category": "Комплексное страхование",
                "description": "Комплексная защита на все случаи жизни",
                "price": 2900,
                "insurance_type": "Комплексное",
                "max_car_age": None,  # Не применимо
                "insurance_amount": None,  # Не применимо
                "insurance_duration": "12 мес.",
                "policy_cost": 2900,
                "risks": "Имущество, Несчастный случай, Критические заболевания",
                "payment_conditions": "единовременно",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": False,
                "compensation_form": "Выплата деньгами",
                "payout_without_certificates": True
            },
            {
                "name": "Всё для бизнеса",
                "category": "Страхование бизнеса",
                "description": "Комплексная программа страхования для бизнеса",
                "price": 0,  # Стоимость расчётная
                "insurance_type": "Бизнес",
                "max_car_age": None,  # Не применимо
                "insurance_amount": None,  # Не применимо
                "insurance_duration": "12 мес.",
                "policy_cost": 0,  # Расчётная
                "risks": "Страхование от несчастных случаев, Гражданская ответственность, Имущество",
                "payment_conditions": "единовременно",
                "client_service_24_7": True,
                "emergency_commissioner": True,
                "tow_truck": False,
                "compensation_form": "Выплата деньгами",
                "payout_without_certificates": True
            }
        ]
    )

def downgrade():
    # Удаляем новые поля
    op.drop_column('products', 'max_car_age')
    op.drop_column('products', 'insurance_amount')
    op.drop_column('products', 'insurance_duration')
    op.drop_column('products', 'policy_cost')
    op.drop_column('products', 'risks')
    op.drop_column('products', 'payment_conditions')
    op.drop_column('products', 'client_service_24_7')
    op.drop_column('products', 'emergency_commissioner')
    op.drop_column('products', 'tow_truck')
    op.drop_column('products', 'compensation_form')
    op.drop_column('products', 'payout_without_certificates')