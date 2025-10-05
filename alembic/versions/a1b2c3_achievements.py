"""add achievements tables

Revision ID: a1b2c3_achievements
Revises: 9d9e_bot_game_stats
Create Date: 2025-09-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3_achievements'
down_revision: Union[str, Sequence[str], None] = '9d9e_bot_game_stats'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'player_achievements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.id'), nullable=False),
        sa.Column('achievement_id', sa.Integer(), sa.ForeignKey('achievements.id'), nullable=False),
        sa.Column('is_unlocked', sa.Boolean(), nullable=True),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('player_id', 'achievement_id', name='uq_player_achievement'),
    )


def downgrade() -> None:
    op.drop_table('player_achievements')
    op.drop_table('achievements')


