"""add_rewies_revised

Revision ID: 31d9c0007360
Revises: a46a4ba47045
Create Date: 2025-03-24 02:51:05.344030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31d9c0007360'
down_revision: Union[str, None] = 'a46a4ba47045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Добавляем новые поля
    op.add_column('reviews', sa.Column('title', sa.String(length=100), nullable=True))
    op.add_column('reviews', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column('reviews', sa.Column('is_anonymous', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('reviews', sa.Column('agreement', sa.Boolean(), nullable=True))
    op.add_column('reviews', sa.Column('review_type', sa.String(length=20), nullable=True))
    op.add_column('reviews', sa.Column('scrollable_text', sa.Text(), nullable=True))

    # Если нужно добавить индексы или ограничения
    op.create_index(op.f('ix_reviews_rating'), 'reviews', ['rating'], unique=False)
    op.create_index(op.f('ix_reviews_review_type'), 'reviews', ['review_type'], unique=False)

def downgrade():
    # Удаляем добавленные поля
    op.drop_index(op.f('ix_reviews_review_type'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_rating'), table_name='reviews')
    
    op.drop_column('reviews', 'scrollable_text')
    op.drop_column('reviews', 'review_type')
    op.drop_column('reviews', 'agreement')
    op.drop_column('reviews', 'is_anonymous')
    op.drop_column('reviews', 'rating')
    op.drop_column('reviews', 'title')