import os
import uuid
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.game.main import WordGame, WordManager, GameState
from src.game.exceptions import InvalidLanguageError
from src.shared.embedding_client import EmbeddingClient
from src.data.loader import load_words, load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
        self.words: Dict[str, Dict[int, str]] = {}

        # Load all configured languages or default
        languages = self.config.get("data", {}).get("languages", {})
        if not languages:
            # Fallback to default if no languages defined
            default_path = self.config["data"]["default_dict"]
            self.words["en"] = load_words(default_path)  # Assume default is EN if not specified
        else:
            for lang, path in languages.items():
                try:
                    self.words[lang] = load_words(path)
                except Exception as e:
                    logger.error(f"Failed to load dictionary for {lang}: {e}")

        # Ensure we have at least one dictionary
        if not self.words:
            raise RuntimeError("No dictionaries loaded")

    async def create_game(
        self, lang: str = "en", seed: str | None = None
    ) -> tuple[str, WordManager, str]:
        session_id = str(uuid.uuid4())

        word_dict = self.words.get(lang)
        if not word_dict:
            logger.warning(f"Language {lang} not found, falling back to first available.")
            lang = list(self.words.keys())[0]
            word_dict = self.words[lang]

        word_manager = WordManager(word_dict, target_words_count=5)
        # Pass seed to init_game. If seed is None, it uses random.
        word_manager.init_game(seed=seed)
        return session_id, word_manager, lang


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


@app.post("/api/game/start", response_model=StartGameResponse)
async def start_game(lang: str = "en", seed: str | None = None):
    manager: GameManager = app.state.game_manager
    client: EmbeddingClient = app.state.embedding_client

    session_id, word_manager, resolved_lang = await manager.create_game(lang=lang, seed=seed)

    game = WordGame(word_manager, client, language=resolved_lang)

    manager.games[session_id] = game

    return StartGameResponse(
        session_id=session_id,
        game_state=GameState(
            current_words=word_manager.get_current_words(),
            removed_words=[],
            added_words=[],
            similarities={},
            round_score=0,
            total_score=0,
            lives=word_manager.lives,
            time_remaining=word_manager.get_time_remaining(),
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
    except InvalidLanguageError as e:
        logger.warning(f"Language error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.warning(f"Invalid move: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error playing round: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/{session_id}/shuffle", response_model=GameState)
async def shuffle_words(session_id: str):
    manager: GameManager = app.state.game_manager

    if session_id not in manager.games:
        raise HTTPException(status_code=404, detail="Game session not found")

    game = manager.games[session_id]

    try:
        game_state = await game.shuffle_words()
        return game_state
    except ValueError as e:
        logger.warning(f"Invalid shuffle request: {e}")
        # Return 400 for logic errors (like not enough score)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error shuffling words: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/{session_id}/stop")
async def stop_game(session_id: str):
    manager: GameManager = app.state.game_manager
    if session_id not in manager.games:
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
