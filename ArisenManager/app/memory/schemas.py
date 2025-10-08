"""Memory schemas for embedding and vector operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmbeddingPayload(BaseModel):
    """Payload for embedding storage."""
    
    chat_id: int = Field(..., description="Chat identifier")
    user_id: int = Field(..., description="User identifier")
    text: str = Field(..., description="Original text content")
    lang: str = Field(default="fa", description="Language code")
    ts: int = Field(..., description="Unix timestamp")


class SearchResult(BaseModel):
    """Vector search result."""
    
    payload: EmbeddingPayload = Field(..., description="Stored payload")
    score: float = Field(..., description="Similarity score")
    id: str = Field(..., description="Point identifier")


class ConfigSchema(BaseModel):
    """Configuration schema for embedding and vector services."""
    
    model: str = Field(default="BAAI/bge-m3", description="HuggingFace model")
    dim: int = Field(default=1024, description="Embedding dimension")
    qdrant_url: str = Field(..., description="Qdrant server URL")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key")
    collection_name: str = Field(default="conv_memory", description="Collection")
    distance_metric: str = Field(default="Cosine", description="Distance metric")
    batch_size: int = Field(default=32, description="Batch processing size")
    max_text_length: int = Field(default=8192, description="Max text length")
    min_text_length: int = Field(default=3, description="Min text length")