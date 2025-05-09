from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

DATABASE_URL = "sqlite:///./chess_game.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class GameModel(Base):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_fen = Column(String, default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    # Store the full PGN to be able to reconstruct game history if needed
    pgn = Column(Text, default="") 
    turn = Column(String, default="white")
    is_checkmate = Column(Boolean, default=False)
    is_stalemate = Column(Boolean, default=False)
    is_insufficient_material = Column(Boolean, default=False)
    is_seventyfive_moves = Column(Boolean, default=False)
    is_fivefold_repetition = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables if they don't exist (for simple setup without migrations initially)
# For production, Alembic should be used.
# Base.metadata.create_all(bind=engine) 
