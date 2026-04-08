import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingClient:
    """Client for interacting with the embedding service."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self._client: httpx.AsyncClient | None = None
        logger.info(f"EmbeddingClient initialized with API URL: {api_url}")

    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        logger.info("EmbeddingClient: Async client opened.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            logger.info("EmbeddingClient: Async client closed.")

    async def get_similarities(self, user_word: str, target_words: list[str]) -> list[float]:
        """Calculate similarities using the API endpoint."""
        request_payload = {
            "text1": user_word,
            "text2": target_words,
            "model": "harrier-oss-v1-0.6b",
            "encoding_format": "float",
        }
        logger.info(
            f"EmbeddingClient: Requesting similarities from {self.api_url}/v1/get_similarity"
        )
        logger.debug(f"EmbeddingClient: Request payload: {request_payload}")

        if not self._client:
            logger.error(
                "EmbeddingClient not initialized before calling get_similarities. Ensure client is used within an async context manager."
            )
            raise RuntimeError("Client not initialized. Use async with context.")

        try:
            response = await self._client.post(
                f"{self.api_url}/v1/get_similarity",
                json=request_payload,
                timeout=10.0,
            )
            logger.debug(
                f"EmbeddingClient: Received raw response (status: {response.status_code}): {response.text}"
            )
            response.raise_for_status()
            json_response = response.json()
            logger.debug(f"EmbeddingClient: Parsed JSON response: {json_response}")
            logger.info(f"EmbeddingClient: Successfully retrieved similarities for '{user_word}'.")
            return json_response["similarity_score"]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"EmbeddingClient: API returned HTTP error {e.response.status_code} for '{user_word}'. Response: {e.response.text}"
            )
            raise RuntimeError(
                f"API request failed with status {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error(
                f"EmbeddingClient: An error occurred while requesting {e.request.url!r}: {e}"
            )
            raise RuntimeError(f"API request failed: {e}") from e
        except Exception as e:
            logger.exception(
                f"EmbeddingClient: An unexpected error occurred during similarity request for '{user_word}'."
            )
            raise RuntimeError(f"An unexpected error occurred: {e}") from e
