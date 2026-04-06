"""Module for running embedding service with Gemma model."""

import os
import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from sentence_transformers import SentenceTransformer

# Debug mode
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.embedding_service.models import (
    EmbeddingRequest,
    EmbeddingResponse,
    SimilarityRequest,
    SimilarityResponse,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

EMBEDDING_DIM = 1024


class EmbeddingService:
    """Service class for managing the embedding model."""

    def __init__(self):
        self.model: SentenceTransformer | None = None
        logger.info("EmbeddingService initialized.")

    async def load_model(self):
        """Load the Gemma model."""
        model_name = "microsoft/harrier-oss-v1-0.6b"  # "tencent/KaLM-Embedding-Gemma3-12B-2511"  # "ibm-granite/granite-embedding-278m-multilingual"  # "all-MiniLM-L6-v2"  # "google/embeddinggemma-300M"
        model_path = os.getenv("MODEL_PATH", model_name)
        logger.info(f"Attempting to load model from: {model_path}")

        try:
            self.model = SentenceTransformer(
                model_path,
                device="cpu",
                truncate_dim=EMBEDDING_DIM,
                backend="torch",
                local_files_only=True,
                model_kwargs={
                    "dtype": "float32",
                    # "device_map": "cpu",
                },
            )
            logger.info(f"Model '{model_name}' loaded successfully from {model_path}.")
        except Exception as e:
            logger.exception(f"Error loading model from {model_path}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def get_model(self):
        """Get the loaded model instance."""
        if self.model is None:
            logger.error("Attempted to get model before it was loaded. Returning RuntimeError.")
            raise RuntimeError("Model not loaded")
        return self.model

    @lru_cache(maxsize=1024)
    def encode_text(self, text: str):
        """Encode a single text string with caching."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        return self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    logger.info("Starting up embedding service lifespan.")
    # Create service instance
    embedding_service = EmbeddingService()
    await embedding_service.load_model()
    app.state.embedding_service = embedding_service
    yield
    logger.info("Shutting down embedding service lifespan.")


app = FastAPI(
    title="Embedding Harrier API",
    description="A FastAPI service providing text embeddings using the Harrier model",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest, req: Request):
    """Create embeddings for the provided text(s)."""
    logger.info(f"Received embedding request for model: {request.model}")
    logger.debug(f"Embedding request details: {request.model_dump_json()}")
    # Convert input to list if it's a single string
    texts = request.input if isinstance(request.input, list) else [request.input]
    logger.debug(f"Number of texts for embedding: {len(texts)}")

    try:
        # Get model and generate embeddings
        model = req.app.state.embedding_service.get_model()
        embeddings = await asyncio.to_thread(
            model.encode, texts, convert_to_numpy=True, normalize_embeddings=True
        )
        logger.debug(f"Generated {len(embeddings)} embeddings.")

        # Format response to match OpenAI's format
        data = [
            {"object": "embedding", "embedding": embedding.tolist(), "index": i}
            for i, embedding in enumerate(embeddings)
        ]

        # Calculate token usage (approximate based on words)
        total_tokens = sum(
            (text.count(" ") + 1 if text else 0) * 1.3 for text in texts
        )  # rough estimate
        logger.info(f"Approximate token usage for embedding: {int(total_tokens)}")

        response = EmbeddingResponse(
            object="list",
            model=request.model,
            data=data,
            usage={
                "prompt_tokens": int(total_tokens),
                "total_tokens": int(total_tokens),
            },
        )
        logger.debug(f"Embedding response: {response.model_dump_json()}")
        return response

    except Exception as e:
        logger.exception(f"Embedding generation failed for request: {request.model_dump_json()}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/v1/get_similarity")
async def get_similarity(request: SimilarityRequest, req: Request) -> SimilarityResponse:
    """Calculate cosine similarity between two texts."""
    logger.info(f"Received similarity request for: {request.text1}, text2: {request.text2}")
    logger.info(f"Similarity request details: {request.model_dump_json()}")
    if not request.text2:
        return SimilarityResponse(similarity_score=[])
    try:
        # Get model and generate embeddings
        model = req.app.state.embedding_service.get_model()
        embedding1 = await asyncio.to_thread(
            model.encode, [request.text1], convert_to_numpy=True, normalize_embeddings=True
        )
        embedding2 = await asyncio.to_thread(
            model.encode, request.text2, convert_to_numpy=True, normalize_embeddings=True
        )

        similarities_tensor = await asyncio.to_thread(model.similarity, embedding1, embedding2)
        similarities = similarities_tensor.tolist()
        logger.info(f"Calculated similarities: {similarities}")

        response = SimilarityResponse(similarity_score=similarities[0])
        logger.info(f"Similarity response: {response.model_dump_json()}")
        return response

    except Exception as e:
        logger.exception(f"Similarity calculation failed for request: {request.model_dump_json()}")
        raise HTTPException(status_code=500, detail=f"Similarity calculation failed: {str(e)}")


@app.get("/health")
async def health_check(req: Request):
    """Health check endpoint for the service."""
    logger.debug("Received health check request.")
    try:
        # Check if model is loaded and accessible
        model = req.app.state.embedding_service.get_model()
        # Try a simple embedding to verify model is working
        _ = await asyncio.to_thread(model.encode, ["test"], convert_to_numpy=True)
        logger.info("Health check successful: Model is loaded and responsive.")
        return {"status": "healthy", "model": "loaded", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"Health check failed: Model not loaded or not responsive. Error: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server for embedding service.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
