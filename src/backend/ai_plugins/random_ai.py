# src/backend/ai_plugins/random_ai.py
import chess
import random
from .base import AIPlugin

class RandomMoveAI(AIPlugin):
    """An AI that picks a random legal move."""

    def get_name(self) -> str:
        return "RandomMoveAI"

    def get_description(self) -> str:
        return "A simple AI that selects a random legal move from the available options."

    def calculate_move(self, board: chess.Board, game_id: str = None) -> chess.Move | None:
        """Calculates a random legal move for the current board state."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None  # No legal moves available
        return random.choice(legal_moves)
