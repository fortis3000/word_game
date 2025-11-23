import os
import sys
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/embedding_service"))
)

from main import app

# Constants for testing
SIMILARITY_SCORE = 0.85
DISSIMILARITY_SCORE = 0.65
HTTP_OK = 200
NUM_EMBEDDINGS_LIST = 2
EMBEDDING_DIMENSION = 768


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
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
    assert len(data["data"][0]["embedding"]) == EMBEDDING_DIMENSION
    assert isinstance(data["data"][0]["embedding"][0], float)


@pytest.mark.parametrize(
    "word_list",
    [
        ["pencil", "pen"],
        ["Kugelschreiber", "Blaustift", "Pferd"],
    ],
)
def test_create_embedding_list_of_strings(test_client, word_list):
    """Test the embedding endpoint with a list of strings."""
    response = test_client.post("/v1/embeddings", json={"input": word_list})
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["object"] == "list"
    assert data["model"] == "embeddinggemma-300m"
    assert len(data["data"]) == len(word_list)
    for i in range(len(word_list)):
        assert data["data"][i]["object"] == "embedding"
        assert len(data["data"][i]["embedding"]) == EMBEDDING_DIMENSION
        assert isinstance(data["data"][i]["embedding"][0], float)


@pytest.mark.parametrize(
    "text1, text2, expected_score",
    [
        ("pencil", "pen", SIMILARITY_SCORE),
        ("Kugelschreiber", "Schreibstift", 0.73),
    ],
)
def test_get_similarity_similar(test_client, text1, text2, expected_score):
    """Test the similarity endpoint."""
    response = test_client.post("/v1/get_similarity", json={"text1": text1, "text2": [text2]})
    assert response.status_code == HTTPStatus.OK.value
    data = response.json()
    assert "similarity_score" in data
    assert data["similarity_score"][0] >= expected_score


@pytest.mark.parametrize(
    "text1, text2, expected_score",
    [
        ("pencil", "horse", DISSIMILARITY_SCORE),
        ("Kugelschreiber", "Pferd", DISSIMILARITY_SCORE),
    ],
)
def test_get_similarity_unsimilar(test_client, text1, text2, expected_score):
    """Test the similarity endpoint."""
    response = test_client.post("/v1/get_similarity", json={"text1": text1, "text2": [text2]})
    assert response.status_code == HTTPStatus.OK.value
    data = response.json()
    assert "similarity_score" in data
    assert data["similarity_score"][0] <= expected_score
