from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4, UUID

from .game import Game

app = FastAPI()

# In-memory storage for games for now
games: dict[UUID, Game] = {}

class NewGameResponse(BaseModel):
    game_id: UUID
    board_fen: str

class MoveRequest(BaseModel):
    uci_move: str

class MoveResponse(BaseModel):
    board_fen: str
    message: str
    game_state: dict

@app.post("/games", response_model=NewGameResponse)
async def create_game():
    game_id = uuid4()
    game = Game()
    games[game_id] = game
    return NewGameResponse(game_id=game_id, board_fen=game.get_board_fen())

@app.post("/games/{game_id}/move", response_model=MoveResponse)
async def submit_move(game_id: UUID, move_request: MoveRequest):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    success, message = game.make_move(move_request.uci_move)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return MoveResponse(
        board_fen=game.get_board_fen(),
        message=message,
        game_state=game.get_game_state()
    )

@app.get("/")
async def root():
    return {"message": "Chess AI Backend"}
