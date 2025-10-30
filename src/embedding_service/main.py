"""Module for running embedding service with Gemma model."""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer


class EmbeddingRequest(BaseModel):
    """Request model for the embedding endpoint."""

    input: str | List[str] = Field(
        description="The text to embed. Can be a string or array of strings."
    )
    model: Optional[str] = Field(
        default="embeddinggemma-300m", description="Model to use for embeddings"
    )
    encoding_format: Optional[str] = Field(
        default="float", description="The format to return the embeddings in"
    )


class SimilarityRequest(BaseModel):
    """Request model for similarity endpoint."""

    text1: str = Field(description="First text for similarity comparison")
    text2: list[str] = Field(description="Second text for similarity comparison")
    model: Optional[str] = Field(
        default="embeddinggemma-300m", description="Model to use for embeddings"
    )
    encoding_format: Optional[str] = Field(
        default="float", description="The format to return the embeddings in"
    )


class SimilarityResponse(BaseModel):
    """Response model for similarity endpoint."""

    similarity_score: list[float] = Field(
        description="Cosine similarity score between the two texts"
    )


class EmbeddingResponse(BaseModel):
    """Response model matching OpenAI's embedding response format."""

    object: str = "list"
    model: str
    data: List[dict]
    usage: dict


class EmbeddingService:
    """Service class for managing the embedding model."""

    def __init__(self):
        self.model = None

    async def load_model(self):
        """Load the Gemma model."""
        model_name = "google/embeddinggemma-300m"
        model_path = os.getenv("MODEL_PATH", model_name)

        try:
            self.model = SentenceTransformer(model_path)
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def get_model(self):
        """Get the loaded model instance."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        return self.model


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application."""
    # Create service instance
    embedding_service = EmbeddingService()
    await embedding_service.load_model()
    app.state.embedding_service = embedding_service
    yield


app = FastAPI(
    title="Embedding Gemma API",
    description="A FastAPI service providing text embeddings using the Gemma model",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest, req: Request):
    """Create embeddings for the provided text(s)."""
    # Convert input to list if it's a single string
    texts = request.input if isinstance(request.input, list) else [request.input]

    try:
        # Get model and generate embeddings
        model = req.app.state.embedding_service.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True)

        # Format response to match OpenAI's format
        data = [
            {"object": "embedding", "embedding": embedding.tolist(), "index": i}
            for i, embedding in enumerate(embeddings)
        ]

        # Calculate token usage (approximate based on words)
        total_tokens = sum(len(text.split()) * 1.3 for text in texts)  # rough estimate

        return EmbeddingResponse(
            object="list",
            model=request.model,
            data=data,
            usage={"prompt_tokens": int(total_tokens), "total_tokens": int(total_tokens)},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/v1/get_similarity")
async def get_similarity(request: SimilarityRequest, req: Request) -> SimilarityResponse:
    """Calculate cosine similarity between two texts."""
    # TODO: test and debug
    # TODO: create client class and unit test it
    try:
        # Get model and generate embeddings
        model = req.app.state.embedding_service.get_model()
        embedding1 = model.encode([request.text1], convert_to_numpy=True)[0]
        embedding2 = model.encode(request.text2, convert_to_numpy=True)

        similarities = model.similarity(embedding1, embedding2).tolist()

        return SimilarityResponse(similarity_score=similarities[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity calculation failed: {str(e)}")


@app.get("/health")
async def health_check(req: Request):
    """Health check endpoint for the service."""
    try:
        # Check if model is loaded and accessible
        model = req.app.state.embedding_service.get_model()
        # Try a simple embedding to verify model is working
        _ = model.encode(["test"], convert_to_numpy=True)
        return {"status": "healthy", "model": "loaded", "version": "1.0.0"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
