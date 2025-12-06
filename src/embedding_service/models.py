from typing import Any

from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Request model for the embedding endpoint."""

    input: str | list[str] = Field(
        description="The text to embed. Can be a string or array of strings."
    )
    model: str = Field(default="embeddinggemma-300m", description="Model to use for embeddings")
    encoding_format: str | None = Field(
        default="float", description="The format to return the embeddings in"
    )


class SimilarityRequest(BaseModel):
    """Request model for similarity endpoint."""

    text1: str = Field(description="First text for similarity comparison")
    text2: list[str] = Field(description="Second text for similarity comparison")
    model: str | None = Field(
        default="embeddinggemma-300m", description="Model to use for embeddings"
    )
    encoding_format: str | None = Field(
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
    data: list[dict[Any, Any]]
    usage: dict[Any, Any]
