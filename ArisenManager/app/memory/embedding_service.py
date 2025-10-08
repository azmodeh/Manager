"""Embedding service using HuggingFace SentenceTransformers."""

import asyncio
import logging
import os
import re
from typing import List

from sentence_transformers import SentenceTransformer

from app.core.text_loader import TextLoader

logger = logging.getLogger(__name__)
text_loader = TextLoader()


class EmbeddingService:
    """Service for generating text embeddings using HuggingFace models."""
    
    def __init__(self) -> None:
        """Initialize embedding service."""
        self._model: SentenceTransformer | None = None
        self._model_name = os.getenv("HUGGINGFACE_MODEL_NAME", "BAAI/bge-m3")
        self._min_length = int(os.getenv("MIN_TEXT_LENGTH", "3"))
        self._max_length = int(os.getenv("MAX_TEXT_LENGTH", "8192"))
    
    async def _load_model(self) -> SentenceTransformer:
        """Load the embedding model lazily."""
        if self._model is None:
            try:
                self._model = await asyncio.to_thread(
                    SentenceTransformer, self._model_name
                )
                logger.info(text_loader.get("log.embedding.model_loaded", 
                                          model=self._model_name))
            except Exception as e:
                logger.error(text_loader.get("err.embedding.model_load", 
                                           error=str(e)))
                raise
        return self._model
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize input text for embedding."""
        if not text or not isinstance(text, str):
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Truncate if too long
        if len(text) > self._max_length:
            text = text[:self._max_length]
        
        return text
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        sanitized = self._sanitize_text(text)
        
        if len(sanitized) < self._min_length:
            logger.warning(text_loader.get("log.embedding.text_too_short", 
                                         length=len(sanitized)))
            return []
        
        try:
            model = await self._load_model()
            embedding = await asyncio.to_thread(
                model.encode,
                sanitized,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            return embedding.astype('float32').tolist()
        
        except Exception as e:
            logger.error(text_loader.get("err.embedding.encode", error=str(e)))
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in parallel."""
        if not texts:
            return []
        
        sanitized_texts = [self._sanitize_text(t) for t in texts]
        valid_texts = [t for t in sanitized_texts if len(t) >= self._min_length]
        
        if not valid_texts:
            logger.warning(text_loader.get("log.embedding.no_valid_texts"))
            return []
        
        try:
            model = await self._load_model()
            embeddings = await asyncio.to_thread(
                model.encode,
                valid_texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                batch_size=32
            )
            return [emb.astype('float32').tolist() for emb in embeddings]
        
        except Exception as e:
            logger.error(text_loader.get("err.embedding.batch_encode", 
                                       error=str(e)))
            raise