# Backend (FastAPI) - Chess AI Web App

This directory contains the backend code for the Chess AI Web App, built with FastAPI and Python. It provides the core chess logic, AI integration, and API endpoints for the frontend to interact with.

## Features
- **FastAPI**: RESTful API for game management and move submission.
- **python-chess**: Handles chess rules, move validation, and board state.
- **AI Plugin System**: Easily extendable system for integrating multiple AI opponents (e.g., random, LLM-based).
- **SQLite Database**: Persists game state and supports saving/loading games.
- **Error Handling**: Basic error handling for AI failures and invalid moves.

## Directory Structure
- `main.py` - FastAPI app entry point and API routes.
- `game.py` - Core chess game logic and state management.
- `database.py` - Database models and persistence logic.
- `ai_plugins/` - AI plugin system and implementations:
  - `base.py` - AI plugin interface.
  - `random_ai.py` - Simple random-move AI.
  - `llm_ai_mock.py` - Mock LLM-based AI (placeholder).
- `alembic/` - Database migrations (managed by Alembic).

## Setup & Running
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run database migrations** (if needed):
   ```bash
   alembic upgrade head
   ```
3. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

## API Overview
- `POST /games/` - Create a new game (optionally vs AI).
- `POST /games/{game_id}/move/` - Submit a move (human or AI).
- `GET /games/{game_id}/` - Get current game state.
- `POST /games/{game_id}/ai-move/` - Request AI to make a move.

## Development Notes
- All backend code is in the `src/backend/` directory.
- AI plugins can be added by implementing the interface in `ai_plugins/base.py`.
- Database migrations are managed with Alembic.

## License
See the root `LICENSE` file.
