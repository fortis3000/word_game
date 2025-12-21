import os
import uuid
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.game.main import WordGame, WordManager, GameState
from src.shared.embedding_client import EmbeddingClient
from src.data.loader import load_words, load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Models
class StartGameResponse(BaseModel):
    session_id: str
    game_state: GameState


class PlayRequest(BaseModel):
    word: str


# Session Manager
class GameManager:
    def __init__(self):
        self.games: Dict[str, WordGame] = {}
        self.clients: Dict[str, EmbeddingClient] = {}
        self.config = load_config()
        self.all_words = load_words(self.config["data"]["default_dict"])

    async def create_game(self) -> tuple[str, WordManager]:
        session_id = str(uuid.uuid4())

        # We need a new client for each game? Or share one?
        # The current implementation of EmbeddingClient uses async context manager.
        # Ideally we should have a singleton client or manage it better,
        # but to respect existing design, let's try to reuse or instantiate per game.
        # Actually, WordGame takes a client. Let's create one client for the app lifespan if possible,
        # but WordGame design might expect ownership.
        # Let's create a single shared client for the application to avoid overhead.

        word_manager = WordManager(self.all_words, target_words_count=5)
        # We will inject the shared client from app.state
        # But wait, WordGame __init__ takes client.

        return session_id, word_manager


# Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources
    logger.info("Initializing Game API...")
    game_manager = GameManager()
    embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8000")
    embedding_client = EmbeddingClient(api_url=embedding_service_url)
    await embedding_client.__aenter__()

    app.state.game_manager = game_manager
    app.state.embedding_client = embedding_client

    yield

    # Cleanup
    await embedding_client.__aexit__(None, None, None)
    logger.info("Game API shutting down...")


app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
# We need to ensure the directory exists first, but we'll assume the next steps create it.
# For now, we will mount it, but we might need to create the dir first to avoid errors.
# We'll handle this in the workflow order.

# API Endpoints


@app.post("/api/game/start", response_model=StartGameResponse)
async def start_game():
    manager: GameManager = app.state.game_manager
    client: EmbeddingClient = app.state.embedding_client

    session_id, word_manager = await manager.create_game()

    game = WordGame(word_manager, client)
    word_manager.init_game()

    manager.games[session_id] = game

    # Get initial state
    # We need to construct the initial state manually or add a method to WordGame/WordManager
    # similar to play_round return but without a move.

    return StartGameResponse(
        session_id=session_id,
        game_state=GameState(
            current_words=word_manager.get_current_words(),
            removed_words=[],
            added_words=[],
            similarities={},
            round_score=0,
            total_score=0,
            game_over=False,
        ),
    )


@app.post("/api/game/{session_id}/play", response_model=GameState)
async def play_round(session_id: str, request: PlayRequest):
    manager: GameManager = app.state.game_manager

    if session_id not in manager.games:
        raise HTTPException(status_code=404, detail="Game session not found")

    game = manager.games[session_id]

    try:
        game_state = await game.play_round(request.word)
        return game_state
    except ValueError as e:
        logger.warning(f"Invalid move: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error playing round: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/{session_id}/stop")
async def stop_game(session_id: str):
    manager: GameManager = app.state.game_manager
    if session_id not in manager.games:
        # If game not found, just return empty/zero stats or 404.
        # For idempotency, maybe just return 0? But 404 is cleaner if we assume valid flow.
        raise HTTPException(status_code=404, detail="Game session not found")

    game = manager.games[session_id]

    # Calculate stats
    words_found = len(game.manager.seen_words) - len(game.manager.current_words)
    summary = {
        "total_score": game.manager.total_score,
        "words_found": max(0, words_found),
        "session_id": session_id,
    }

    del manager.games[session_id]
    return summary


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="src/game/static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
