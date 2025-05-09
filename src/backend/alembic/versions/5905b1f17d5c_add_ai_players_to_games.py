"""add_ai_players_to_games

Revision ID: 5905b1f17d5c
Revises: 02bc706977f2
Create Date: 2025-05-09 14:49:44.133444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5905b1f17d5c'
down_revision: Union[str, None] = '02bc706977f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('games', sa.Column('player_white_ai', sa.String(), nullable=True))
    op.add_column('games', sa.Column('player_black_ai', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('games', 'player_black_ai')
    op.drop_column('games', 'player_white_ai')
