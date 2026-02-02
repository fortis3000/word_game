from http import HTTPStatus
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient
from src.embedding_service.main import app

# Constants for testing
SIMILARITY_SCORE = 0.85
DISSIMILARITY_SCORE = 0.65
HTTP_OK = 200
NUM_EMBEDDINGS_LIST = 2
EMBEDDING_DIMENSION = 768


@pytest.fixture
def mock_sentence_transformer():
    """Mock the SentenceTransformer model."""
    with patch("src.embedding_service.main.SentenceTransformer") as MockClass:
        model = MagicMock()

        # Define some base vectors for deterministic similarity
        # normalized vectors
        v_pencil = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)
        v_pencil[0] = 1.0

        v_pen = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)
        v_pen[0] = 0.9
        v_pen[1] = 0.4358  # sqrt(1 - 0.9^2) approx, to make it unit length

        v_horse = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)
        v_horse[2] = 1.0

        word_map = {
            "pencil": v_pencil,
            "pen": v_pen,
            "horse": v_horse,
            "Kugelschreiber": v_pencil,  # Treat as synonym to pencil
            "Schreibstift": v_pen,  # Treat as synonym to pen
            "Pferd": v_horse,
            "Blaustift": v_pencil,
        }

        def encode_side_effect(sentences, convert_to_numpy=True, normalize_embeddings=True):
            is_single_string = isinstance(sentences, str)
            if is_single_string:
                sentences = [sentences]

            embeddings = []
            for s in sentences:
                if s in word_map:
                    embeddings.append(word_map[s])
                else:
                    # Random default
                    rng = np.random.default_rng(hash(s) % 2**32)
                    v = rng.random(EMBEDDING_DIMENSION, dtype=np.float32)
                    norm = np.linalg.norm(v)
                    embeddings.append(v / norm)

            result = np.array(embeddings)
            if is_single_string:
                return result[0]
            return result

        model.encode.side_effect = encode_side_effect

        def similarity_side_effect(emb1, emb2):
            # emb1: (M, D), emb2: (N, D)
            # result: (M, N)
            return np.dot(emb1, emb2.T)

        model.similarity.side_effect = similarity_side_effect

        MockClass.return_value = model
        yield model


@pytest.fixture
def test_client(mock_sentence_transformer):
    """Create a test client for the FastAPI app."""
    # We need to ensure the app's lifespan is triggered with the mock in place
    with TestClient(app) as client:
        yield client


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == HTTP_OK
    assert response.json() == {
        "status": "healthy",
        "model": "loaded",
        "version": "1.0.0",
    }


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
    # v_pencil . v_pen = 0.9. Check if 0.9 >= 0.85 (SIMILARITY_SCORE) -> True
    # Kugelschreiber (pencil) . Schreibstift (pen) = 0.9. >= 0.73 -> True
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
    # v_pencil . v_horse = 0. <= 0.65 -> True
    assert data["similarity_score"][0] <= expected_score

def test_get_similarity_empty_list(test_client):
    """Test the similarity endpoint with empty list."""
    response = test_client.post("/v1/get_similarity", json={"text1": "test", "text2": []})
    assert response.status_code == HTTPStatus.OK.value
    data = response.json()
    assert data["similarity_score"] == []
