from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from .game import Game
from .database import SessionLocal, engine, GameModel, get_db # Updated imports
from .ai_plugins import load_plugins, get_available_plugins, get_plugin # New imports for AI plugins

# Base.metadata.create_all(bind=engine) # Alembic handles this

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    load_plugins() # Load AI plugins on startup

class CreateGameRequest(BaseModel):
    player_white_ai: str | None = None
    player_black_ai: str | None = None

class NewGameResponse(BaseModel):
    game_id: UUID
    board_fen: str
    # Add other initial game state info if needed
    turn: str
    pgn: str
    player_white_ai: str | None = None
    player_black_ai: str | None = None

class MoveRequest(BaseModel):
    uci_move: str

class MoveResponse(BaseModel):
    game_id: UUID
    board_fen: str
    message: str
    game_state: dict

class GameStateResponse(BaseModel):
    game_id: UUID
    board_fen: str
    pgn: str
    turn: str
    player_white_ai: str | None = None
    player_black_ai: str | None = None
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    is_seventyfive_moves: bool
    is_fivefold_repetition: bool
    legal_moves: list[str]


@app.post("/games", response_model=NewGameResponse)
async def create_game(request: CreateGameRequest, db: Session = Depends(get_db)):
    game_logic = Game() # Handles chess logic, not directly persisted
    
    # Validate AI names if provided
    if request.player_white_ai and not get_plugin(request.player_white_ai):
        raise HTTPException(status_code=400, detail=f"AI plugin '{request.player_white_ai}' not found for white player.")
    if request.player_black_ai and not get_plugin(request.player_black_ai):
        raise HTTPException(status_code=400, detail=f"AI plugin '{request.player_black_ai}' not found for black player.")

    new_db_game = GameModel(
        id=uuid4(), # Generate new UUID for the game
        board_fen=game_logic.get_board_fen(),
        pgn="", # Initial PGN is empty
        turn="white", # Initial turn
        player_white_ai=request.player_white_ai,
        player_black_ai=request.player_black_ai
    )
    db.add(new_db_game)
    db.commit()
    db.refresh(new_db_game)
    
    return NewGameResponse(
        game_id=new_db_game.id,
        board_fen=new_db_game.board_fen,
        turn=new_db_game.turn,
        pgn=new_db_game.pgn,
        player_white_ai=new_db_game.player_white_ai,
        player_black_ai=new_db_game.player_black_ai
    )

@app.get("/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: UUID, db: Session = Depends(get_db)):
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Reconstruct game logic to get legal moves, etc.
    game_logic = Game()
    game_logic.board.set_fen(db_game.board_fen)
    # If PGN is stored and python-chess can load PGN to reconstruct history for legal moves:
    # game_logic.board.reset()
    # for move_san in db_game.pgn.split(): # This is a simplified PGN parsing
    #     if "." in move_san: continue # Skip move numbers
    #     try:
    #         move = game_logic.board.parse_san(move_san)
    #         game_logic.board.push(move)
    #     except ValueError:
    #         pass # Potentially log error if PGN is malformed

    current_game_state = game_logic.get_game_state()

    return GameStateResponse(
        game_id=db_game.id,
        board_fen=db_game.board_fen,
        pgn=db_game.pgn,
        turn=current_game_state["turn"],
        player_white_ai=db_game.player_white_ai,
        player_black_ai=db_game.player_black_ai,
        is_checkmate=current_game_state["is_checkmate"],
        is_stalemate=current_game_state["is_stalemate"],
        is_insufficient_material=current_game_state["is_insufficient_material"],
        is_seventyfive_moves=current_game_state["is_seventyfive_moves"],
        is_fivefold_repetition=current_game_state["is_fivefold_repetition"],
        legal_moves=current_game_state["legal_moves"]
    )

@app.post("/games/{game_id}/move", response_model=MoveResponse)
async def submit_move(game_id: UUID, move_request: MoveRequest, db: Session = Depends(get_db)):
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    game_logic = Game()
    # Load current board state from DB FEN
    game_logic.board.set_fen(db_game.board_fen)
    # TODO: Consider loading full game history from PGN if needed for complex validation
    # or if the Game class internally relies on full history.
    # For now, FEN is sufficient for python-chess to validate next move.

    success, message = game_logic.make_move(move_request.uci_move)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Update DB record
    db_game.board_fen = game_logic.get_board_fen()
    # Update PGN - this is a simplified way; a proper PGN generator would be better
    # For python-chess, you might need to build PGN move by move
    # This requires the Game class to track moves or for us to parse the last move.
    # For simplicity, let's assume the Game object can provide the last move in SAN
    # or we append the UCI move. A proper PGN would include move numbers.
    last_move_san = game_logic.board.peek().uci() # Gets the last move in UCI, convert to SAN if possible
    try:
        # Attempt to get SAN for PGN. This requires the board to be in the state *before* the move was made.
        # This is tricky. For now, let's just append UCI, or better, have Game class manage PGN.
        # A better approach: game_logic.get_last_move_san() if implemented
        # Or, if game_logic.board.move_stack is not empty:
        if game_logic.board.move_stack:
            move_obj = game_logic.board.pop() # get the move
            san_move = game_logic.board.san(move_obj) # get its SAN
            game_logic.board.push(move_obj) # put it back
            
            if db_game.pgn:
                db_game.pgn += f" {san_move}"
            else:
                db_game.pgn = san_move
        else: # Fallback if stack is empty or SAN conversion fails
             if db_game.pgn:
                db_game.pgn += f" {move_request.uci_move}" # Fallback to UCI
             else:
                db_game.pgn = move_request.uci_move


    except Exception: # Broad except for safety, ideally more specific
        if db_game.pgn:
            db_game.pgn += f" {move_request.uci_move}" # Fallback to UCI
        else:
            db_game.pgn = move_request.uci_move


    current_game_state = game_logic.get_game_state()
    db_game.turn = current_game_state["turn"]
    db_game.is_checkmate = current_game_state["is_checkmate"]
    db_game.is_stalemate = current_game_state["is_stalemate"]
    db_game.is_insufficient_material = current_game_state["is_insufficient_material"]
    db_game.is_seventyfive_moves = current_game_state["is_seventyfive_moves"]
    db_game.is_fivefold_repetition = current_game_state["is_fivefold_repetition"]
    
    db.commit()
    db.refresh(db_game)
    
    return MoveResponse(
        game_id=db_game.id,
        board_fen=db_game.board_fen,
        message=message,
        game_state=current_game_state
    )

# New endpoint to list available AI plugins
class AIPluginInfo(BaseModel):
    name: str
    description: str

@app.get("/ai-plugins", response_model=list[AIPluginInfo])
async def list_ai_plugins():
    plugins = get_available_plugins()
    if not plugins:
        # This case can be hit if load_plugins() hasn't found any or there was an issue.
        # Depending on strictness, could raise HTTPException or return empty list with log.
        print("No AI plugins loaded or available.")
    return plugins

@app.get("/")
async def root():
    return {"message": "Chess AI Backend"}

@app.post("/games/{game_id}/ai-move", response_model=MoveResponse) # New endpoint for AI moves
async def submit_ai_move(game_id: UUID, db: Session = Depends(get_db)):
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    game_logic = Game()
    game_logic.board.set_fen(db_game.board_fen)

    current_turn_color = "white" if game_logic.board.turn == chess.WHITE else "black"
    ai_plugin_name = None
    if current_turn_color == "white" and db_game.player_white_ai:
        ai_plugin_name = db_game.player_white_ai
    elif current_turn_color == "black" and db_game.player_black_ai:
        ai_plugin_name = db_game.player_black_ai

    if not ai_plugin_name:
        raise HTTPException(status_code=400, detail=f"No AI configured for the current player ({current_turn_color}) or it's not AI's turn.")

    ai_plugin = get_plugin(ai_plugin_name)
    if not ai_plugin:
        # This should ideally not happen if validated at game creation, but good for robustness
        raise HTTPException(status_code=500, detail=f"Configured AI plugin '{ai_plugin_name}' not found.")

    # AI calculates the move
    ai_chess_move = None
    try:
        # Potentially add a timeout mechanism here in the future if AI calls are long-running
        ai_chess_move = ai_plugin.calculate_move(game_logic.board, game_id=str(db_game.id))
    except Exception as e:
        # Log the exception from the AI plugin
        print(f"Error during AI ({ai_plugin_name}) move calculation for game {game_id}: {e}")
        # Optionally, store this error state in the DB or notify admins
        raise HTTPException(status_code=500, detail=f"AI plugin '{ai_plugin_name}' encountered an internal error: {str(e)}")

    if not ai_chess_move:
        # This could mean AI resigns, or can't find a move (e.g. in checkmate/stalemate already, though board state should reflect that)
        # Or an error in AI logic.
        # For now, treat as if AI cannot make a move, which might be an error or game end.
        # The game state itself (checkmate, stalemate) should be the source of truth for game end.
        raise HTTPException(status_code=400, detail=f"AI '{ai_plugin_name}' did not provide a move. Game state: {game_logic.get_game_state()}")

    # Validate and apply the AI's move to the game logic
    # The AI plugin should return a chess.Move object. We need its UCI string.
    uci_move_str = ai_chess_move.uci()
    success, message = game_logic.make_move(uci_move_str)
    
    if not success:
        # This would indicate an issue with the AI providing an illegal move, or a bug.
        raise HTTPException(status_code=500, detail=f"AI '{ai_plugin_name}' provided an illegal move '{uci_move_str}'. Error: {message}. Board: {game_logic.board.fen()}")
    
    # Update DB record (similar to human move)
    db_game.board_fen = game_logic.get_board_fen()
    # PGN update logic (copied and adapted from human move, consider refactoring to a helper)
    try:
        if game_logic.board.move_stack:
            move_obj = game_logic.board.pop() 
            san_move = game_logic.board.san(move_obj) 
            game_logic.board.push(move_obj) 
            db_game.pgn = (db_game.pgn + f" {san_move}").lstrip()
        else:
            db_game.pgn = (db_game.pgn + f" {uci_move_str}").lstrip()
    except Exception:
        db_game.pgn = (db_game.pgn + f" {uci_move_str}").lstrip()

    current_game_state_dict = game_logic.get_game_state()
    db_game.turn = current_game_state_dict["turn"]
    db_game.is_checkmate = current_game_state_dict["is_checkmate"]
    db_game.is_stalemate = current_game_state_dict["is_stalemate"]
    db_game.is_insufficient_material = current_game_state_dict["is_insufficient_material"]
    db_game.is_seventyfive_moves = current_game_state_dict["is_seventyfive_moves"]
    db_game.is_fivefold_repetition = current_game_state_dict["is_fivefold_repetition"]
    
    db.commit()
    db.refresh(db_game)
    
    return MoveResponse(
        game_id=db_game.id,
        board_fen=db_game.board_fen,
        message=f"AI {ai_plugin_name} moved: {uci_move_str}. {message}",
        game_state=current_game_state_dict
    )
