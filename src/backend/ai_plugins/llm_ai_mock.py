# src/backend/ai_plugins/llm_ai_mock.py
import chess
import random
from .base import AIPlugin

class LLMAIMock(AIPlugin):
    """Placeholder for an LLM-based AI. Currently returns a random move."""

    def get_name(self) -> str:
        return "LLM_Mock_AI"

    def get_description(self) -> str:
        return "A mock placeholder for an LLM-based AI. Makes random moves."

    def calculate_move(self, board: chess.Board, game_id: str = None) -> chess.Move | None:
        """Calculates a move. For now, it returns a random legal move."""
        print(f"LLM_Mock_AI ({game_id=}): Calculating move (mock implementation - random). Board FEN: {board.fen()}")
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            print(f"LLM_Mock_AI ({game_id=}): No legal moves available.")
            return None
        
        chosen_move = random.choice(legal_moves)
        print(f"LLM_Mock_AI ({game_id=}): Chosen move: {chosen_move.uci()}")
        return chosen_move
