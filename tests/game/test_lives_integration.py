import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from src.game.api import app, GameManager
from src.game.main import WordGame, WordManager
from src.shared.embedding_client import EmbeddingClient


@pytest.fixture
def client():
    return TestClient(app)


@patch("src.game.api.GameManager")
@patch("src.game.api.EmbeddingClient")
def test_integration_game_over_lives(mock_emb_cls, mock_gm_cls, client):
    # 1. Setup proper mocks for the full chain
    mock_gm = MagicMock(spec=GameManager)
    app.state.game_manager = mock_gm

    # We need a real WordManager logic, but with controlled words
    words = {0: "apple", 1: "banana"}
    wm = WordManager(words, target_words_count=2, initial_lives=1)
    wm.init_game(seed=42)  # Deterministic

    # Mock EmbeddingClient to always return low similarity (fail)
    mock_emb = AsyncMock(spec=EmbeddingClient)
    # Return low similarity for 2 words
    mock_emb.get_similarities.return_value = [0.1, 0.1]

    # Create the game instance using real WordManager
    game = WordGame(wm, mock_emb, similarity_threshold=0.6)

    # Register game in manager
    mock_gm.games = {"sess_lives": game}

    # 2. Play a round that fails
    response = client.post("/api/game/sess_lives/play", json={"word": "nothing"})

    assert response.status_code == 200
    data = response.json()

    # 3. Verify state
    assert data["lives"] == 0
    assert data["game_over"]
    assert data["round_score"] == 0
    assert len(data["removed_words"]) == 0
