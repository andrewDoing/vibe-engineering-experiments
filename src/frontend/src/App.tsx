import React, { useState, useEffect } from 'react';
import './App.css';
import ChessboardComponent from './components/ChessboardComponent';
import { Chess } from 'chess.js';

// Define interfaces for API responses
interface AIPluginInfo {
  name: string;
  description: string;
}

interface NewGameResponse {
  game_id: string;
  board_fen: string;
  turn: string;
  pgn: string;
  player_white_ai: string | null;
  player_black_ai: string | null;
}

interface MoveResponse {
  game_id: string;
  board_fen: string;
  message: string;
  game_state: any; // Define more specifically if needed
}

interface GameStateResponse {
  game_id: string;
  board_fen: string;
  pgn: string;
  turn: string;
  player_white_ai: string | null;
  player_black_ai: string | null;
  is_checkmate: boolean;
  is_stalemate: boolean;
  is_insufficient_material: boolean;
  is_seventyfive_moves: boolean;
  is_fivefold_repetition: boolean;
  legal_moves: string[];
}

const API_BASE_URL = 'http://localhost:8000'; // Backend API URL

function App() {
  const [game, setGame] = useState(new Chess());
  const [fen, setFen] = useState(game.fen());
  const [lastMove, setLastMove] = useState<[string, string] | null>(null);
  const [squareStyles, setSquareStyles] = useState({});
  const [gameId, setGameId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('Click \'New Game\' to start.');
  const [pgn, setPgn] = useState<string>("");
  const [turn, setTurn] = useState<string>("white");
  const [legalMoves, setLegalMoves] = useState<string[]>([]); 
  const [aiPlugins, setAiPlugins] = useState<AIPluginInfo[]>([]); // State for AI plugins
  const [selectedWhiteAI, setSelectedWhiteAI] = useState<string | null>(null); // State for selected white AI
  const [selectedBlackAI, setSelectedBlackAI] = useState<string | null>(null); // State for selected black AI
  const [isAiThinking, setIsAiThinking] = useState<boolean>(false); // State to indicate AI is thinking

  // Fetch AI plugins on component mount
  useEffect(() => {
    const fetchAiPlugins = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/ai-plugins`);
        if (!response.ok) {
          throw new Error(`Error fetching AI plugins: ${response.statusText}`);
        }
        const data: AIPluginInfo[] = await response.json();
        setAiPlugins(data);
        if (data.length > 0) {
          // Optionally pre-select if desired, or leave as null for "Human"
        }
      } catch (error) {
        console.error('Failed to fetch AI plugins:', error);
        setStatusMessage(`Failed to fetch AI plugins: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    fetchAiPlugins();
  }, []);

  // Function to fetch and update game state from backend
  const fetchGameState = async (currentGameId: string) => {
    if (!currentGameId) return;
    try {
      // setStatusMessage('Fetching game state...'); // Can be too noisy, let higher-level functions set status
      const response = await fetch(`${API_BASE_URL}/games/${currentGameId}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error fetching game state: ${response.statusText} - ${errorText}`);
      }
      const data: GameStateResponse = await response.json();
      
      const updatedGameInstance = new Chess(data.board_fen);
      setGame(updatedGameInstance);
      setFen(data.board_fen);
      setGameId(data.game_id); // Ensure gameId is also updated/confirmed
      setPgn(data.pgn);
      setTurn(data.turn);
      setLegalMoves(data.legal_moves);
      // Update status message based on fetched game state
      let currentStatus = `Game ID: ${data.game_id}. It's ${data.turn}'s turn.`;
      if (updatedGameInstance.isCheckmate()) currentStatus += " Checkmate!";
      else if (updatedGameInstance.isStalemate()) currentStatus += " Stalemate!";
      else if (updatedGameInstance.isDraw()) currentStatus += " Draw!";
      setStatusMessage(currentStatus);

      console.log('Game state fetched:', data);
      console.log('Legal moves:', data.legal_moves); // Acknowledge legalMoves

      // Check if it's AI's turn after fetching state (e.g., after a human move)
      const currentPlayerIsWhite = updatedGameInstance.turn() === 'w';
      const whiteIsAI = data.player_white_ai && data.player_white_ai !== "human";
      const blackIsAI = data.player_black_ai && data.player_black_ai !== "human";

      if ((currentPlayerIsWhite && whiteIsAI) || (!currentPlayerIsWhite && blackIsAI)) {
        if (!isAiThinking) { // Prevent re-triggering if already thinking from a previous action
          await triggerAiMove(data.game_id);
        }
      }

    } catch (error) {
      console.error('Failed to fetch game state:', error);
      setStatusMessage(`Failed to fetch game state: ${error instanceof Error ? error.message : String(error)}`);
    }
  };
  
  // Function to create a new game via the backend
  const createNewGame = async () => {
    try {
      setStatusMessage('Creating new game...');
      setIsAiThinking(false); // Reset AI thinking state
      const requestBody: { player_white_ai?: string; player_black_ai?: string } = {};
      if (selectedWhiteAI && selectedWhiteAI !== "human") {
        requestBody.player_white_ai = selectedWhiteAI;
      }
      if (selectedBlackAI && selectedBlackAI !== "human") {
        requestBody.player_black_ai = selectedBlackAI;
      }

      const response = await fetch(`${API_BASE_URL}/games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error creating game: ${response.statusText} - ${errorText}`);
      }
      const data: NewGameResponse = await response.json();
      setGameId(data.game_id);
      const newGameInstance = new Chess(data.board_fen);
      setGame(newGameInstance);
      setFen(data.board_fen);
      setLastMove(null);
      setSquareStyles({});
      setPgn(data.pgn); // Initialize PGN
      setTurn(data.turn); // Initialize turn
      // Fetch full game state to get legal moves etc. and potentially trigger AI if it's AI's first move
      await fetchGameState(data.game_id);
      // setStatusMessage(`New game started (ID: ${data.game_id}). It's ${data.turn}'s turn.`); // fetchGameState will set this
      console.log('New game created:', data);
    } catch (error) {
      console.error('Failed to create new game:', error);
      setStatusMessage(`Failed to create new game: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleMove = (sourceSquare: string, targetSquare: string, piece?: string): boolean => {
    if (!gameId) {
      setStatusMessage('No active game. Please start a new game.');
      console.error('No game ID available to make a move.');
      return false; // Cannot make a move
    }

    // Use a temporary copy of the game for local validation
    const tempGame = new Chess(fen);
    const localMoveResult = tempGame.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q' // Default to queen promotion
    });

    if (localMoveResult === null) {
      console.log('Illegal move attempt (local validation):', sourceSquare, targetSquare);
      setStatusMessage('Illegal move.');
      return false; // Local validation failed, disallow move on UI
    }

    // Local validation passed. Optimistically update UI.
    setFen(tempGame.fen());
    setLastMove([sourceSquare, targetSquare]);
    setStatusMessage('Submitting move...');

    // Asynchronously send the move to the backend
    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/games/${gameId}/move`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ uci_move: `${sourceSquare}${targetSquare}` }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: `Error submitting move: ${response.statusText}` }));
          throw new Error(errorData.detail || `Error submitting move: ${response.statusText}`);
        }

        const data: MoveResponse = await response.json();
        
        // Backend confirmed the human move. Fetch state, which will also trigger AI if it's their turn.
        await fetchGameState(data.game_id);
        // setStatusMessage(data.message || `Move successful. It's ${updatedGameInstance.turn() === 'w' ? 'White' : 'Black'}\'s turn.`); // fetchGameState handles status
        console.log('Move successful (backend):', data);

      } catch (error) {
        console.error('Error making move (backend):', error);
        setStatusMessage(`Error: ${error instanceof Error ? error.message : String(error)}. Reverting local move.`);
        // Revert optimistic UI update because backend failed
        // Revert to the FEN of the last confirmed state (held in the 'game' object)
        setFen(game.fen()); 
        setLastMove(null); // Clear highlighting of the failed move
        // Consider if game object also needs reverting if its state was speculatively changed
        // In this setup, 'game' is only updated on backend success, so it's already correct.
      }
    })();

    return true; // Local validation passed, allow move on the board UI
  };

  // Function to trigger AI move
  const triggerAiMove = async (currentGameId: string) => {
    if (!currentGameId) return;
    console.log("Attempting to trigger AI move for game:", currentGameId);
    setIsAiThinking(true);
    setStatusMessage('AI is thinking...');
    try {
      const response = await fetch(`${API_BASE_URL}/games/${currentGameId}/ai-move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `AI move failed: ${response.statusText}` }));
        throw new Error(errorData.detail || `AI move failed: ${response.statusText}`);
      }
      const aiMoveData: MoveResponse = await response.json();
      setStatusMessage(aiMoveData.message || 'AI move processed.');
      // Fetch game state to reflect AI's move and check if it's human's turn again or another AI's turn
      await fetchGameState(currentGameId);
    } catch (error) {
      console.error('Error triggering AI move:', error);
      setStatusMessage(`Error during AI move: ${error instanceof Error ? error.message : String(error)}`);
      // Even if AI move fails, fetch game state to ensure UI is consistent with backend
      await fetchGameState(currentGameId);
    } finally {
      setIsAiThinking(false);
    }
  };

  useEffect(() => {
    if (lastMove) {
      setSquareStyles({
        [lastMove[0]]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' },
        [lastMove[1]]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' }
      });
    } else {
      setSquareStyles({});
    }
  }, [lastMove]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Chess AI Web App</h1>

        {/* AI Selection UI */}
        <div className="ai-selection">
          <div>
            <label htmlFor="white-ai-select">White: </label>
            <select 
              id="white-ai-select" 
              value={selectedWhiteAI || "human"} 
              onChange={(e) => setSelectedWhiteAI(e.target.value === "human" ? null : e.target.value)}
            >
              <option value="human">Human</option>
              {aiPlugins.map(plugin => (
                <option key={plugin.name} value={plugin.name}>{plugin.name} ({plugin.description})</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="black-ai-select">Black: </label>
            <select 
              id="black-ai-select" 
              value={selectedBlackAI || "human"} 
              onChange={(e) => setSelectedBlackAI(e.target.value === "human" ? null : e.target.value)}
            >
              <option value="human">Human</option>
              {aiPlugins.map(plugin => (
                <option key={plugin.name} value={plugin.name}>{plugin.name} ({plugin.description})</option>
              ))}
            </select>
          </div>
        </div>

        <ChessboardComponent 
          fen={fen} 
          onMove={handleMove} 
          boardWidth={560} 
          squareStyles={squareStyles} 
        />
        <p>Status: {statusMessage}</p>
        {isAiThinking && <p><i>AI is thinking...</i></p>} {/* Show AI thinking message */}
        <p>Current FEN: {fen}</p>
        <p>Turn: {turn}</p> {/* Display turn */}
        <p>PGN: {pgn}</p> {/* Display PGN */}
        {/* Game outcome messages are now part of statusMessage or can be derived from 'game' object */}
        {/* {game.isGameOver() && <p>Game Over!</p>} */}
        {/* {game.isCheckmate() && <p>Checkmate!</p>} */}
        {/* {game.isStalemate() && <p>Stalemate!</p>} */}
        {/* {game.isDraw() && <p>Draw!</p>} */}
        <button onClick={createNewGame}>New Game</button>
        {gameId && <button onClick={() => fetchGameState(gameId)}>Refresh Game State</button>} {/* Button to manually refresh */}
      </header>
    </div>
  );
}

export default App;
