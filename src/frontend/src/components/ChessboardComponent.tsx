import React from 'react';
import { Chessboard } from 'react-chessboard';
import './ChessboardComponent.css';

interface ChessboardComponentProps {
  fen: string; // Forsyth-Edwards Notation for board state
  onMove?: (sourceSquare: string, targetSquare: string, piece?: string) => boolean; // Callback for when a piece is moved
  boardWidth?: number;
  arePiecesDraggable?: boolean;
  squareStyles?: { [square: string]: React.CSSProperties }; // Added to accept custom square styles
  // Add other props as needed from react-chessboard documentation
}

const ChessboardComponent: React.FC<ChessboardComponentProps> = ({
  fen,
  onMove,
  boardWidth = 400, // Default width
  arePiecesDraggable = true,
  squareStyles = {}, // Default to empty object
}) => {
  const handlePieceDrop = (
    sourceSquare: string,
    targetSquare: string,
    piece: string
  ): boolean => {
    if (onMove) {
      return onMove(sourceSquare, targetSquare, piece);
    }
    console.log(`Piece dropped from ${sourceSquare} to ${targetSquare} (${piece}) - no external validation.`);
    return true; 
  };

  return (
    <div className="chessboard-container">
      <Chessboard
        id="BasicChessboard"
        position={fen}
        onPieceDrop={handlePieceDrop} 
        boardWidth={boardWidth}
        arePiecesDraggable={arePiecesDraggable}
        customSquareStyles={squareStyles} // Pass to react-chessboard
        // Customization options can be added here
      />
    </div>
  );
};

export default ChessboardComponent;