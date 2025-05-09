from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware # Add this import

from .game import Game
from .database import SessionLocal, engine, GameModel, get_db # Updated imports
from .ai_plugins import load_plugins, get_available_plugins, get_plugin # Updated imports

# Base.metadata.create_all(bind=engine) # Alembic handles this

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allows React dev server
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    load_plugins() # Load AI plugins on startup

class CreateGameRequest(BaseModel):
    player_white_ai: str | None = None
    player_black_ai: str | None = None

class NewGameResponse(BaseModel):
    game_id: UUID
    board_fen: str
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

# New Pydantic model for AI plugin info
class AIPluginInfo(BaseModel):
    name: str
    description: str

# New endpoint to list available AI plugins
@app.get("/ai/plugins", response_model=list[AIPluginInfo])
async def list_ai_plugins():
    plugins = get_available_plugins() # This returns list[dict[str, str]]
    return [AIPluginInfo(name=p["name"], description=p["description"]) for p in plugins]


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
        pgn=game_logic.get_pgn(), # Use PGN from Game class, includes headers
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
    # Pass PGN string to Game constructor
    game_logic = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)
    # The Game class's __init__ should handle setting up the board correctly.
    # If board_fen in db is the source of truth for current position, ensure Game reflects that.
    # game_logic.board.set_fen(db_game.board_fen) # This might be redundant if Game.__init__ is robust

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

    # Initialize Game logic with current FEN and PGN from DB
    game_logic = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)

    # Make the human's move
    human_move_success, human_move_message = game_logic.make_move(move_request.uci_move)
    
    if not human_move_success:
        raise HTTPException(status_code=400, detail=human_move_message)
    
    # Update DB with the state after human's move
    current_game_state_after_human = game_logic.get_game_state()
    db_game.board_fen = current_game_state_after_human["board_fen"]
    db_game.pgn = current_game_state_after_human["pgn"]
    db_game.turn = current_game_state_after_human["turn"]
    db_game.is_checkmate = current_game_state_after_human["is_checkmate"]
    db_game.is_stalemate = current_game_state_after_human["is_stalemate"]
    db_game.is_insufficient_material = current_game_state_after_human["is_insufficient_material"]
    db_game.is_seventyfive_moves = current_game_state_after_human["is_seventyfive_moves"]
    db_game.is_fivefold_repetition = current_game_state_after_human["is_fivefold_repetition"]
    
    db.commit()
    db.refresh(db_game)

    # Now, check if AI needs to move
    game_over_after_human = (
        db_game.is_checkmate or 
        db_game.is_stalemate or 
        db_game.is_insufficient_material or 
        db_game.is_seventyfive_moves or 
        db_game.is_fivefold_repetition
    )

    final_game_state_for_response = current_game_state_after_human
    ai_move_message_suffix = ""

    if not game_over_after_human:
        active_ai_name = None
        if db_game.turn == "white" and db_game.player_white_ai:
            active_ai_name = db_game.player_white_ai
        elif db_game.turn == "black" and db_game.player_black_ai:
            active_ai_name = db_game.player_black_ai
        
        if active_ai_name:
            ai_plugin = get_plugin(active_ai_name)
            if ai_plugin:
                # AI uses the same game_logic instance, which has the updated board & PGN
                ai_chess_move = ai_plugin.calculate_move(game_logic.board, game_id=str(game_id))

                if ai_chess_move:
                    ai_move_success, ai_move_message_from_logic = game_logic.make_move(ai_chess_move.uci())
                    
                    if ai_move_success:
                        current_game_state_after_ai = game_logic.get_game_state()
                        db_game.board_fen = current_game_state_after_ai["board_fen"]
                        db_game.pgn = current_game_state_after_ai["pgn"]
                        db_game.turn = current_game_state_after_ai["turn"]
                        db_game.is_checkmate = current_game_state_after_ai["is_checkmate"]
                        db_game.is_stalemate = current_game_state_after_ai["is_stalemate"]
                        db_game.is_insufficient_material = current_game_state_after_ai["is_insufficient_material"]
                        db_game.is_seventyfive_moves = current_game_state_after_ai["is_seventyfive_moves"]
                        db_game.is_fivefold_repetition = current_game_state_after_ai["is_fivefold_repetition"]
                        
                        db.commit()
                        db.refresh(db_game)
                        final_game_state_for_response = current_game_state_after_ai
                        ai_move_message_suffix = f" AI ({active_ai_name}) responded with {ai_chess_move.uci()}."
                    else:
                        print(f"AI ({active_ai_name}) failed to make a valid move {ai_chess_move.uci()}: {ai_move_message_from_logic}")
                        ai_move_message_suffix = f" AI ({active_ai_name}) failed to move ({ai_chess_move.uci()}): {ai_move_message_from_logic}."
                else:
                    print(f"AI ({active_ai_name}) did not provide a move.")
                    ai_move_message_suffix = f" AI ({active_ai_name}) provided no move."
            else:
                print(f"AI plugin '{active_ai_name}' not found during AI turn.")
                ai_move_message_suffix = f" AI plugin '{active_ai_name}' not found."
    
    return MoveResponse(
        game_id=db_game.id,
        board_fen=final_game_state_for_response["board_fen"],
        message=human_move_message + ai_move_message_suffix,
        game_state=final_game_state_for_response
    )

# Renamed from request_ai_move and removed trailing slash from path
@app.post("/games/{game_id}/ai-move", response_model=MoveResponse)
async def trigger_ai_move(game_id: UUID, db: Session = Depends(get_db)):
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    game_over = (
        db_game.is_checkmate or db_game.is_stalemate or db_game.is_insufficient_material or
        db_game.is_seventyfive_moves or db_game.is_fivefold_repetition
    )
    if game_over:
        # Return current game state if game is over, instead of raising HTTP 400
        # This allows frontend to fetch final state if it calls this endpoint unknowingly.
        game_logic_for_state = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)
        current_state = game_logic_for_state.get_game_state()
        return MoveResponse(
            game_id=db_game.id,
            board_fen=current_state["board_fen"],
            message="Game is already over.",
            game_state=current_state
        )

    active_ai_name = None
    if db_game.turn == "white" and db_game.player_white_ai:
        active_ai_name = db_game.player_white_ai
    elif db_game.turn == "black" and db_game.player_black_ai:
        active_ai_name = db_game.player_black_ai
    
    if not active_ai_name:
        # It's not an AI's turn. Return current state with a message.
        game_logic_for_state = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)
        current_state = game_logic_for_state.get_game_state()
        return MoveResponse(
            game_id=db_game.id,
            board_fen=current_state["board_fen"],
            message="It's not an AI's turn or no AI is assigned to the current player.",
            game_state=current_state
        )

    ai_plugin = get_plugin(active_ai_name)
    if not ai_plugin:
        # AI plugin not found. Return current state with an error message.
        game_logic_for_state = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)
        current_state = game_logic_for_state.get_game_state()
        return MoveResponse(
            game_id=db_game.id,
            board_fen=current_state["board_fen"],
            message=f"AI plugin '{active_ai_name}' not found.",
            game_state=current_state
        )

    game_logic = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn)
    ai_chess_move = ai_plugin.calculate_move(game_logic.board, game_id=str(game_id))

    if not ai_chess_move:
        current_state = game_logic.get_game_state()
        return MoveResponse(
            game_id=db_game.id,
            board_fen=current_state["board_fen"],
            message=f"AI ({active_ai_name}) did not provide a move.",
            game_state=current_state
        )

    ai_move_success, ai_move_message_from_logic = game_logic.make_move(ai_chess_move.uci())
    
    if not ai_move_success:
        # AI proposed an invalid move. Return state before this attempt.
        current_state_before_invalid_ai_move = Game(board_fen=db_game.board_fen, pgn_str=db_game.pgn).get_game_state()
        return MoveResponse(
            game_id=db_game.id,
            board_fen=current_state_before_invalid_ai_move["board_fen"],
            message=f"AI ({active_ai_name}) proposed an invalid move {ai_chess_move.uci()}: {ai_move_message_from_logic}",
            game_state=current_state_before_invalid_ai_move
        )

    current_game_state_after_ai = game_logic.get_game_state()
    db_game.board_fen = current_game_state_after_ai["board_fen"]
    db_game.pgn = current_game_state_after_ai["pgn"]
    db_game.turn = current_game_state_after_ai["turn"]
    db_game.is_checkmate = current_game_state_after_ai["is_checkmate"]
    db_game.is_stalemate = current_game_state_after_ai["is_stalemate"]
    db_game.is_insufficient_material = current_game_state_after_ai["is_insufficient_material"]
    db_game.is_seventyfive_moves = current_game_state_after_ai["is_seventyfive_moves"]
    db_game.is_fivefold_repetition = current_game_state_after_ai["is_fivefold_repetition"]
    
    db.commit()
    db.refresh(db_game)
    
    return MoveResponse(
        game_id=db_game.id,
        board_fen=current_game_state_after_ai["board_fen"],
        message=f"AI ({active_ai_name}) moved {ai_chess_move.uci()}. {ai_move_message_from_logic}",
        game_state=current_game_state_after_ai
    )

# Endpoint to get available AI plugins (already defined above, just for context)
# @app.get("/ai/plugins", response_model=list[AIPluginInfo])
# async def list_ai_plugins():
#     plugins = get_available_plugins()
#     return [AIPluginInfo(name=p["name"], description=p["description"]) for p in plugins]
