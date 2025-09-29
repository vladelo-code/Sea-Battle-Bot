"""add bot game stats

Revision ID: 9d9e_bot_game_stats
Revises: c2c59db636bb
Create Date: 2025-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d9e_bot_game_stats'
down_revision: Union[str, Sequence[str], None] = 'c2c59db636bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bot_game_stats',
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('losses', sa.Integer(), nullable=True),
        sa.Column('last_played_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['players.id']),
        sa.PrimaryKeyConstraint('player_id', 'difficulty')
    )


def downgrade() -> None:
    op.drop_table('bot_game_stats')


