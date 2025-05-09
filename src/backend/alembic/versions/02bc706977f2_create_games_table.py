"""create_games_table

Revision ID: 02bc706977f2
Revises: 
Create Date: 2025-05-09 14:40:12.793531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # Import for UUID type
import uuid # Import for default uuid value


# revision identifiers, used by Alembic.
revision: str = '02bc706977f2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'games',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('board_fen', sa.String(), nullable=False, server_default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'),
        sa.Column('pgn', sa.Text(), nullable=False, server_default=''),
        sa.Column('turn', sa.String(), nullable=False, server_default='white'),
        sa.Column('is_checkmate', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_stalemate', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_insufficient_material', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_seventyfive_moves', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_fivefold_repetition', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('games')
