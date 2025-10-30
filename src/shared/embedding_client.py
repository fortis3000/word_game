import httpx


class EmbeddingClient:
    """Client for interacting with the embedding service."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get_similarities(self, user_word: str, target_words: list[str]) -> list[float]:
        """Calculate similarities using the API endpoint."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context.")

        try:
            response = await self._client.post(
                f"{self.api_url}/v1/get_similarity",
                json={
                    "text1": user_word,
                    "text2": target_words,
                    "model": "embeddinggemma-300m",
                    "encoding_format": "float",
                },
                timeout=10.0,  # Add timeout
            )
            response.raise_for_status()
            return response.json()["similarity_score"]
        except httpx.HTTPError as e:
            raise RuntimeError(f"API request failed: {e}") from e
