import chess
import chess.pgn
import io # For reading PGN string

class Game:
    def __init__(self, board_fen=None, pgn_str=None): # Added pgn_str
        self.board = chess.Board()
        self.pgn_game = None # Initialize later

        if pgn_str:
            try:
                pgn_io = io.StringIO(pgn_str)
                parsed_game = chess.pgn.read_game(pgn_io)
                if parsed_game:
                    self.pgn_game = parsed_game
                    # Board state should be at the end of the PGN's main line
                    # Replay moves onto a fresh board to ensure correct state
                    self.board = self.pgn_game.board() # Initial board from headers
                    for move in self.pgn_game.mainline_moves():
                        self.board.push(move)
                    self.current_pgn_node = self.pgn_game.end() or self.pgn_game # Point to the last node or root
                else: # PGN parsing failed or empty PGN
                    self._initialize_empty_pgn_game()
                    if board_fen: self.board.set_fen(board_fen)
            except Exception as e:
                print(f"Error loading PGN: \'{pgn_str[:50]}...\'. Error: {e}. Initializing new game state.")
                self._initialize_empty_pgn_game()
                if board_fen:
                    try:
                        self.board.set_fen(board_fen)
                        # If starting from FEN after PGN error, ensure PGN reflects this
                        self.pgn_game.headers["FEN"] = board_fen
                        self.pgn_game.setup(self.board) # Re-setup PGN game from this FEN
                        self.current_pgn_node = self.pgn_game
                    except ValueError:
                        print(f"Warning: Invalid FEN \'{board_fen}\' after PGN load error. Using default board.")
                        # Board is already default, PGN is fresh
                
        elif board_fen: # No PGN string, just FEN
            self._initialize_empty_pgn_game()
            try:
                self.board.set_fen(board_fen)
                self.pgn_game.headers["FEN"] = board_fen
                # self.pgn_game.setup(self.board) # This makes the board the starting position of the PGN
                # Let's ensure current_pgn_node is the root for a game starting from FEN
                self.current_pgn_node = self.pgn_game 
            except ValueError:
                print(f"Warning: Invalid FEN string \'{board_fen}\' provided. Using default board.")
                # self.board is already chess.Board(), pgn_game is fresh via _initialize_empty_pgn_game
        else: # Neither FEN nor PGN
            self._initialize_empty_pgn_game()

    def _initialize_empty_pgn_game(self):
        self.pgn_game = chess.pgn.Game()
        self.pgn_game.headers["Event"] = "Chess AI Web App Game"
        # TODO: Add other headers like Site, Date, White, Black from db_game if available
        self.current_pgn_node = self.pgn_game

    def make_move(self, uci_move: str) -> tuple[bool, str]:
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                self.board.push(move) # Push move to board first
                # Add move to PGN tree.
                if not self.current_pgn_node: # Should have been initialized
                    print("Error: current_pgn_node is None. Re-initializing PGN game.")
                    # This case should ideally not be hit if __init__ is correct
                    # Attempt to recover or raise error
                    if self.pgn_game:
                        self.current_pgn_node = self.pgn_game.end() or self.pgn_game
                    else: # pgn_game itself is None, critical error
                         self._initialize_empty_pgn_game() # Last resort
                
                self.current_pgn_node = self.current_pgn_node.add_main_variation(move)
                return True, f"Move {uci_move} successful."
            else:
                return False, f"Invalid move: {uci_move}. Not a legal move."
        except ValueError:
            return False, f"Invalid move format: {uci_move}."
        except Exception as e: # Catch other potential errors during PGN manipulation
            print(f"Error during make_move PGN update: {e}")
            # Attempt to proceed with board move if PGN fails, or return error
            # For now, let's assume if PGN fails, the move itself is problematic for consistency
            return False, f"Error processing move {uci_move} due to PGN update issue."


    def get_board_fen(self) -> str:
        return self.board.fen()

    def get_pgn(self) -> str:
        if not self.pgn_game: return ""
        # Export PGN without variations for simplicity, include headers
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        return self.pgn_game.accept(exporter)

    def get_game_state(self) -> dict:
        # Ensure PGN is up-to-date if it's part of the state
        current_pgn = self.get_pgn()
        return {
            "board_fen": self.board.fen(),
            "pgn": current_pgn,
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_insufficient_material": self.board.is_insufficient_material(),
            "is_seventyfive_moves": self.board.is_seventyfive_moves(),
            "is_fivefold_repetition": self.board.is_fivefold_repetition(),
            # Game over can also be due to is_variant_win, is_variant_loss, is_variant_draw
            "is_game_over": self.board.is_game_over(claim_draw=True), # claim_draw for 50-move, 3-fold
            "legal_moves": [move.uci() for move in self.board.legal_moves]
        }
