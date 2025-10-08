from typing import Optional
from pydantic import BaseModel
from ..utils.text_loader import text_loader

# Cache text lookups at module level
_TEXTS = {
    "default_lang": text_loader.get_text("vector_memory.defaults.language"),
    "default_model": text_loader.get_text("vector_memory.defaults.model"),
    "default_collection": "memories"
}


class EmbeddingPayload(BaseModel):
    chat_id: int
    user_id: int
    text: str
    lang: str = _TEXTS["default_lang"]
    ts: int


class SearchResult(BaseModel):
    payload: EmbeddingPayload
    score: float
    id: str


class MemoryPayload(BaseModel):
    group_id: int
    user_id: int
    user_name: str
    timestamp: int
    text: str
    model: str = _TEXTS["default_model"]
    language: str = _TEXTS["default_lang"]


class ContextResult(BaseModel):
    text: str
    user_id: int
    user_name: str
    ts: int
    score: float


class ConfigSchema(BaseModel):
    model: str = _TEXTS["default_model"]
    dim: int = 1024
    qdrant_url: str
    qdrant_api_key: Optional[str] = None
    collection_name: str = _TEXTS["default_collection"]
    distance_metric: str = "Cosine"
    batch_size: int = 32
    max_text_length: int = 8192
    min_text_length: int = 3