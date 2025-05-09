# Plan: Chess AI Web App

## Phase 1: Project Setup & Backend Core
- [x] Task 1.1: Initialize project structure (`src` directory).
- [x] Task 1.2: Setup Python backend with FastAPI.
- [x] Task 1.3: Integrate `python-chess` for core chess logic (board representation, move validation, game state).
- [x] Task 1.4: Implement basic API endpoints for game creation and move submission.
- [x] Task 1.5: Setup SQLite for game persistence.
- [x] Task 1.6: Implement basic game persistence logic (save/load game state).

## Phase 2: AI Integration - Backend
- [x] Task 2.1: Design and implement the AI plugin system architecture.
- [x] Task 2.2: Implement a simple rule-based Python AI (e.g., random move or basic heuristics).
- [x] Task 2.3: Integrate the simple Python AI into the plugin system.
- [x] Task 2.4: Implement an LLM-based AI (placeholder/mock integration initially).
- [x] Task 2.5: Integrate the LLM-based AI into the plugin system.
- [x] Task 2.6: Update API endpoints to allow AI selection for a game.
- [x] Task 2.7: Implement basic error handling for AI failures/timeouts in the backend.

## Phase 3: Frontend Development - React
- [x] Task 3.1: Setup React frontend application.
- [x] Task 3.2: Create a 2D chessboard component.
- [x] Task 3.3: Implement chessboard interactivity (e.g., drag and drop or click-to-move for pieces).
- [x] Task 3.4: Implement move input and highlighting.
- [x] Task 3.5: Connect frontend to backend APIs for game creation and move submission.
- [x] Task 3.6: Display game state from the backend.

## Phase 4: Core Gameplay Features
- [x] Task 4.1: Implement Human vs AI mode.
  - [x] Task 4.1.1: Allow user to select an AI opponent.
  - [x] Task 4.1.2: Enable user to make moves against the selected AI.
- [ ] Task 4.2: Implement AI vs AI mode.
  - [ ] Task 4.2.1: Allow user to select two AIs to play against each other.
  - [ ] Task 4.2.2: Display the AI vs AI match progressing automatically.
- [ ] Task 4.3: Implement runtime AI swapping.
  - [ ] Task 4.3.1: Allow user to change the AI opponent during a game.
- [ ] Task 4.4: Implement game persistence UI.
  - [ ] Task 4.4.1: UI for saving the current game.
  - [ ] Task 4.4.2: UI for loading/resuming a previous game.

## Phase 5: Refinement and Deployment Preparation
- [ ] Task 5.1: Enhance error handling and UI feedback for AI errors/timeouts.
- [ ] Task 5.2: Basic styling and usability improvements for the UI.
- [ ] Task 5.3: Write unit/integration tests for critical backend and frontend components.
- [ ] Task 5.4: Dockerize the frontend application.
- [ ] Task 5.5: Dockerize the backend application.
- [ ] Task 5.6: Create `docker-compose.yml` for easy local setup.
- [ ] Task 5.7: Write README updates for setup and running the application.

## Success Criteria:
- All MVP features are implemented and functional:
    - Interactive 2D chessboard UI.
    - Human vs AI mode with at least two AIs (one Python, one LLM-based).
    - AI vs AI mode.
    - Runtime AI swapping.
    - Game persistence (save/load).
    - Basic error handling for AI operations.
- The application is Dockerized and can be run locally using `docker-compose`.
- Basic documentation (README) for setup and usage is available.
- Code is organized in the `src` directory.
- Plan and notes files are up-to-date in `docs/plans` and `docs/notes`.
