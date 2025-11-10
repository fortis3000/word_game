from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.shared.embedding_client import EmbeddingClient

# Constants for testing
TEST_SIMILARITY_SCORE_1 = 0.9
TEST_SIMILARITY_SCORE_2 = 0.8
TEST_TIMEOUT = 10.0


@pytest.fixture
def embedding_client():
    return EmbeddingClient(api_url="http://test-api.com")


@pytest.mark.asyncio
async def test_embedding_client_init(embedding_client):
    assert embedding_client.api_url == "http://test-api.com"
    assert embedding_client._client is None


@pytest.mark.asyncio
async def test_embedding_client_context_manager():
    with patch("httpx.AsyncClient") as mock_async_client_class:
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value = mock_client_instance

        client = EmbeddingClient()
        async with client as c:
            assert c._client is mock_client_instance
            mock_async_client_class.assert_called_once()
        mock_client_instance.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_get_similarities_success(embedding_client):
    with patch("httpx.AsyncClient") as mock_async_client_class:
        mock_client_instance = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={"similarity_score": [TEST_SIMILARITY_SCORE_1, TEST_SIMILARITY_SCORE_2]}
        )
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_client_instance.post.return_value = mock_response
        mock_async_client_class.return_value = mock_client_instance

        async with embedding_client as client:
            similarities = await client.get_similarities("word1", ["word2", "word3"])
            assert similarities == [TEST_SIMILARITY_SCORE_1, TEST_SIMILARITY_SCORE_2]
            mock_client_instance.post.assert_called_once_with(
                "http://test-api.com/v1/get_similarity",
                json={
                    "text1": "word1",
                    "text2": ["word2", "word3"],
                    "model": "embeddinggemma-300m",
                    "encoding_format": "float",
                },
                timeout=TEST_TIMEOUT,
            )


@pytest.mark.asyncio
async def test_get_similarities_http_error(embedding_client):
    with patch("httpx.AsyncClient") as mock_async_client_class:
        mock_client_instance = AsyncMock()
        mock_async_client_class.return_value = mock_client_instance
        mock_client_instance.post.side_effect = httpx.RequestError(
            "Test error", request=httpx.Request("POST", "http://test-api.com")
        )

        async with embedding_client as client:
            with pytest.raises(RuntimeError, match="API request failed"):
                await client.get_similarities("word1", ["word2"])


@pytest.mark.asyncio
async def test_get_similarities_client_not_initialized(embedding_client):
    with pytest.raises(RuntimeError, match="Client not initialized"):
        await embedding_client.get_similarities("word1", ["word2"])
