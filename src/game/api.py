import os
import uuid
import time
import secrets
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.game.main import WordGame, WordManager, GameState
from src.shared.embedding_client import EmbeddingClient
from src.data.loader import load_words, load_config
from src.utils.logger import get_logger
from src.game.metrics import (
    http_request_duration_seconds,
    http_requests_total,
    game_errors_total,
    game_words_submitted_total,
)

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
    ) -> tuple[str, WordManager]:
        session_id = str(uuid.uuid4())

        word_dict = self.words.get(lang)
        if not word_dict:
            logger.warning(f"Language {lang} not found, falling back to first available.")
            lang = list(self.words.keys())[0]
            word_dict = self.words[lang]

        word_manager = WordManager(word_dict, target_words_count=5)
        # Pass seed to init_game. If seed is None, it uses random.
        word_manager.init_game(seed=seed)
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
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Prometheus metrics endpoint
security = HTTPBasic()

PROMETHEUS_USER = os.getenv("PROMETHEUS_USER", "prom_user")
PROMETHEUS_PASSWORD = os.getenv("PROMETHEUS_PASSWORD", "changeme_in_production")


def verify_metrics_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, PROMETHEUS_USER)
    correct_password = secrets.compare_digest(credentials.password, PROMETHEUS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/metrics", include_in_schema=False)
async def metrics(username: str = Depends(verify_metrics_auth)):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def get_client_type(user_agent: str) -> str:
    """Extract general client type from User-Agent to avoid PII but keep stats."""
    ua_lower = user_agent.lower()
    if "telegram" in ua_lower:
        return "telegram"
    elif "mobi" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        return "mobile_browser"
    elif "mozilla" in ua_lower or "chrome" in ua_lower or "safari" in ua_lower:
        return "desktop_browser"
    return "unknown"


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.perf_counter() - start_time

    # Get client type
    user_agent = request.headers.get("user-agent", "")
    client_type = get_client_type(user_agent)

    # Prevent cardinality explosion by grouping all 404s into a generic path
    if response.status_code == 404:
        path = "/unmatched_route"
    else:
        route = request.scope.get("route")
        if route:
            path = route.path
        else:
            path = request.url.path

    # Record metrics (skip metrics endpoint itself and static files to avoid noise)
    if (
        not path.startswith("/metrics")
        and not path.startswith("/css")
        and not path.startswith("/js")
        and not path.startswith("/img")
    ):
        http_requests_total.labels(
            method=request.method,
            path=path,
            status_code=response.status_code,
            client_type=client_type,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            path=path,
            status_code=response.status_code,
            client_type=client_type,
        ).observe(duration)

    return response


@app.post("/api/game/start", response_model=StartGameResponse)
async def start_game(lang: str = "en", seed: str | None = None):
    manager: GameManager = app.state.game_manager
    client: EmbeddingClient = app.state.embedding_client

    session_id, word_manager = await manager.create_game(lang=lang, seed=seed)

    game = WordGame(word_manager, client)

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
async def play_round(session_id: str, request_data: PlayRequest, request: Request):
    manager: GameManager = app.state.game_manager

    client_type = get_client_type(request.headers.get("user-agent", ""))

    if session_id not in manager.games:
        game_errors_total.labels(error_type="session_not_found", client_type=client_type).inc()
        raise HTTPException(status_code=404, detail="Game session not found")

    game = manager.games[session_id]

    try:
        # Track word submission metrics and log the word itself
        game_words_submitted_total.labels(client_type=client_type).inc()
        logger.info("Word submitted", extra={"word": request_data.word, "client_type": client_type})

        game_state = await game.play_round(request_data.word)
        return game_state
    except ValueError as e:
        logger.warning(f"Invalid move: {e}")
        game_errors_total.labels(error_type="invalid_move", client_type=client_type).inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error playing round: {e}")
        game_errors_total.labels(error_type="internal_error", client_type=client_type).inc()
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
