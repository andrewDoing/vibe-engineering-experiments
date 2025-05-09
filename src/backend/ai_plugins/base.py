# src/backend/ai_plugins/base.py
from abc import ABC, abstractmethod
import chess

class AIPlugin(ABC):
    """Abstract base class for AI chess plugins."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique name of the AI plugin."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return a brief description of the AI plugin."""
        pass

    @abstractmethod
    def calculate_move(self, board: chess.Board, game_id: str = None) -> chess.Move | None:
        """Calculate the next best move for the current board state.

        Args:
            board: The current chess.Board object.
            game_id: Optional game identifier, if the AI needs context or to persist state.

        Returns:
            A chess.Move object representing the AI's chosen move, or None if no move can be made.
        """
        pass
