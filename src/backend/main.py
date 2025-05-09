from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from .game import Game
from .database import SessionLocal, engine, GameModel, get_db # Updated imports
from .ai_plugins import load_plugins, get_available_plugins # New imports for AI plugins

# Base.metadata.create_all(bind=engine) # Alembic handles this

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    load_plugins() # Load AI plugins on startup

class NewGameResponse(BaseModel):
    game_id: UUID
    board_fen: str
    # Add other initial game state info if needed
    turn: str
    pgn: str

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
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    is_seventyfive_moves: bool
    is_fivefold_repetition: bool
    legal_moves: list[str]


@app.post("/games", response_model=NewGameResponse)
async def create_game(db: Session = Depends(get_db)):
    game_logic = Game() # Handles chess logic, not directly persisted
    
    new_db_game = GameModel(
        id=uuid4(), # Generate new UUID for the game
        board_fen=game_logic.get_board_fen(),
        pgn="", # Initial PGN is empty
        turn="white" # Initial turn
        # Other fields will use defaults from GameModel
    )
    db.add(new_db_game)
    db.commit()
    db.refresh(new_db_game)
    
    return NewGameResponse(
        game_id=new_db_game.id,
        board_fen=new_db_game.board_fen,
        turn=new_db_game.turn,
        pgn=new_db_game.pgn
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
