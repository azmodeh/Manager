"""Qdrant vector database client for memory storage."""

import asyncio
import logging
import os
import time
import uuid
from typing import List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException

from app.core.text_loader import TextLoader
from app.memory.schemas import EmbeddingPayload, SearchResult

logger = logging.getLogger(__name__)
text_loader = TextLoader()


class VectorMemoryDB:
    """Qdrant-based vector memory database."""
    
    def __init__(self) -> None:
        """Initialize Qdrant client."""
        self._client: AsyncQdrantClient | None = None
        self._url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self._api_key = os.getenv("QDRANT_API_KEY")
        self._default_collection = "conv_memory"
    
    async def _get_client(self) -> AsyncQdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            try:
                self._client = AsyncQdrantClient(
                    url=self._url,
                    api_key=self._api_key,
                    timeout=30.0
                )
                logger.info(text_loader.get("log.qdrant.client_connected", 
                                          url=self._url))
            except Exception as e:
                logger.error(text_loader.get("err.qdrant.connection", 
                                           error=str(e)))
                raise
        return self._client
    
    async def ensure_collection(
        self, 
        name: str = "conv_memory", 
        dim: int = 1024, 
        distance: str = "Cosine"
    ) -> bool:
        """Ensure collection exists with proper configuration."""
        try:
            client = await self._get_client()
            
            # Check if collection exists
            collections = await client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if name in existing:
                logger.info(text_loader.get("log.qdrant.collection_exists", 
                                          name=name))
                return True
            
            # Create collection
            await client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=getattr(models.Distance, distance.upper())
                )
            )
            
            logger.info(text_loader.get("log.qdrant.collection_created", 
                                      name=name, dim=dim))
            return True
            
        except ResponseHandlingException as e:
            logger.error(text_loader.get("err.qdrant.collection_create", 
                                       error=str(e)))
            return False
        except Exception as e:
            logger.error(text_loader.get("err.qdrant.collection_setup", 
                                       error=str(e)))
            return False
    
    async def upsert_memory(
        self,
        chat_id: int,
        user_id: int,
        text: str,
        vector: List[float],
        lang: str = "fa",
        collection: str = "conv_memory"
    ) -> bool:
        """Store memory vector with metadata."""
        if not vector or len(vector) == 0:
            logger.warning(text_loader.get("log.qdrant.empty_vector"))
            return False
        
        try:
            client = await self._get_client()
            
            point_id = str(uuid.uuid4())
            payload = EmbeddingPayload(
                chat_id=chat_id,
                user_id=user_id,
                text=text,
                lang=lang,
                ts=int(time.time())
            )
            
            await client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload.model_dump()
                    )
                ]
            )
            
            logger.debug(text_loader.get("log.qdrant.upsert_success", 
                                       chat_id=chat_id))
            return True
            
        except Exception as e:
            logger.error(text_loader.get("err.qdrant.upsert", error=str(e)))
            return False
    
    async def search_memory(
        self,
        chat_id: int,
        query_vector: List[float],
        top_k: int = 5,
        collection: str = "conv_memory"
    ) -> List[SearchResult]:
        """Search for similar memories in chat context."""
        if not query_vector or len(query_vector) == 0:
            return []
        
        try:
            client = await self._get_client()
            
            results = await client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="chat_id",
                            match=models.MatchValue(value=chat_id)
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True
            )
            
            search_results = []
            for result in results:
                if result.payload:
                    payload = EmbeddingPayload(**result.payload)
                    search_results.append(SearchResult(
                        payload=payload,
                        score=result.score,
                        id=str(result.id)
                    ))
            
            logger.debug(text_loader.get("log.qdrant.search_results", 
                                       count=len(search_results)))
            return search_results
            
        except Exception as e:
            logger.error(text_loader.get("err.qdrant.search", error=str(e)))
            return []
    
    async def compact(
        self, 
        days_keep: int = 90, 
        collection: str = "conv_memory"
    ) -> int:
        """Remove old memories beyond retention period."""
        cutoff_ts = int(time.time()) - (days_keep * 24 * 3600)
        
        try:
            client = await self._get_client()
            
            # Delete old points
            result = await client.delete(
                collection_name=collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="ts",
                                range=models.Range(lt=cutoff_ts)
                            )
                        ]
                    )
                )
            )
            
            deleted_count = getattr(result, 'operation_id', 0)
            logger.info(text_loader.get("log.qdrant.compact_complete", 
                                      count=deleted_count))
            return deleted_count
            
        except Exception as e:
            logger.error(text_loader.get("err.qdrant.compact", error=str(e)))
            return 0
    
    async def close(self) -> None:
        """Close Qdrant client connection."""
        if self._client:
            await self._client.close()
            self._client = None