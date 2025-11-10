import os
import sys
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/embedding_service"))
)

from main import app

# Constants for testing
EMBEDDING_1 = [0.1, 0.2, 0.3]
EMBEDDING_2 = [0.4, 0.5, 0.6]
SIMILARITY_SCORE = 0.9
HTTP_OK = 200
HTTP_SERVICE_UNAVAILABLE = 503
NUM_EMBEDDINGS_LIST = 2


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with patch("main.SentenceTransformer") as mock_sentence_transformer:
        mock_model = MagicMock()

        def encode_side_effect(texts, convert_to_numpy=True):
            if len(texts) == 1:
                return [np.array(EMBEDDING_1)]
            return [np.array(EMBEDDING_1), np.array(EMBEDDING_2)]

        mock_model.encode.side_effect = encode_side_effect
        mock_model.similarity.return_value = np.array([[SIMILARITY_SCORE]])
        mock_sentence_transformer.return_value = mock_model
        with TestClient(app) as client:
            yield client


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "healthy", "model": "loaded", "version": "1.0.0"}


def test_create_embedding_single_string(test_client):
    """Test the embedding endpoint with a single string."""
    response = test_client.post("/v1/embeddings", json={"input": "test string"})
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["object"] == "list"
    assert data["model"] == "embeddinggemma-300m"
    assert len(data["data"]) == 1
    assert data["data"][0]["object"] == "embedding"
    assert data["data"][0]["embedding"] == EMBEDDING_1


def test_create_embedding_list_of_strings(test_client):
    """Test the embedding endpoint with a list of strings."""
    response = test_client.post(
        "/v1/embeddings", json={"input": ["test string 1", "test string 2"]}
    )
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["object"] == "list"
    assert data["model"] == "embeddinggemma-300m"
    assert len(data["data"]) == NUM_EMBEDDINGS_LIST


def test_get_similarity(test_client):
    """Test the similarity endpoint."""
    response = test_client.post("/v1/get_similarity", json={"text1": "test1", "text2": ["test2"]})
    assert response.status_code == HTTPStatus.OK.value
    data = response.json()
    assert "similarity_score" in data
    assert data["similarity_score"] == [SIMILARITY_SCORE]
