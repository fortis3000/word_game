import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from src.game.api import app, GameManager
from src.game.main import WordGame, GameState


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_game_manager():
    manager = MagicMock(spec=GameManager)
    manager.games = {}
    manager.config = {"data": {"default_dict": "dummy_path"}}
    manager.all_words = {1: "apple", 2: "banana", 3: "cherry"}
    return manager


@pytest.fixture
def mock_embedding_client():
    client = AsyncMock()
    client.get_similarities.return_value = [0.9, 0.5, 0.1]
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None
    return client


@patch("src.game.api.GameManager")
@patch("src.game.api.EmbeddingClient")
def test_start_game(mock_emb_cls, mock_gm_cls, client):
    # Mock dependencies
    app.state.game_manager = mock_gm_cls.return_value
    app.state.embedding_client = mock_emb_cls.return_value

    mock_gm = app.state.game_manager
    # Setup create_game to return a dummy session and manager
    mock_word_manager = MagicMock()
    mock_word_manager.get_current_words.return_value = ["apple", "banana"]
    mock_word_manager.get_time_remaining.return_value = 180.0
    mock_gm.create_game = AsyncMock(return_value=("sess_123", mock_word_manager))

    response = client.post("/api/game/start")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess_123"
    assert data["game_state"]["current_words"] == ["apple", "banana"]
    assert "session_id" in data


@patch("src.game.api.GameManager")
def test_play_round_not_found(mock_gm_cls, client):
    app.state.game_manager = mock_gm_cls.return_value
    app.state.game_manager.games = {}

    response = client.post("/api/game/invalid_sess/play", json={"word": "test"})
    assert response.status_code == 404


@patch("src.game.api.GameManager")
@patch("src.game.api.WordGame")
def test_play_round_success(mock_game_cls, mock_gm_cls, client):
    # Setup Mock Game
    mock_game = AsyncMock(spec=WordGame)
    mock_game.play_round.return_value = GameState(
        current_words=["banana", "cherry"],
        removed_words=["apple"],
        added_words=["cherry"],
        similarities={"apple": 0.9},
        round_score=90,
        total_score=90,
        lives=5,
        time_remaining=180.0,
        game_over=False,
    )

    # Setup Manager
    app.state.game_manager = mock_gm_cls.return_value
    app.state.game_manager.games = {"sess_123": mock_game}

    response = client.post("/api/game/sess_123/play", json={"word": "fruit"})

    assert response.status_code == 200
    data = response.json()
    assert data["round_score"] == 90
    assert "apple" in data["removed_words"]


@patch("src.game.api.GameManager")
def test_stop_game(mock_gm_cls, client):
    # Setup mock manager and inject into app state
    mock_gm = MagicMock(spec=GameManager)

    # Create a mock game with necessary attributes
    mock_game = MagicMock()
    mock_game.manager.seen_words = ["apple", "banana"]
    mock_game.manager.current_words = ["banana"]
    mock_game.manager.total_score = 10

    mock_gm.games = {"sess_123": mock_game}
    app.state.game_manager = mock_gm

    response = client.post("/api/game/sess_123/stop")

    assert response.status_code == 200
    assert response.json() == {
        "session_id": "sess_123",
        "total_score": 10,
        "words_found": 1,
    }
    assert "sess_123" not in mock_gm.games
