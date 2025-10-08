"""Qdrant vector database client for memory storage."""

import logging
import os
import time
import uuid
from typing import List, Optional, Set

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException

from ..utils.text_loader import text_loader
from .schemas import EmbeddingPayload, SearchResult

logger = logging.getLogger(__name__)


class VectorMemoryDB:
    """Qdrant-based vector memory database."""
    
    def __init__(self) -> None:
        """Initialize Qdrant client."""
        self._client: AsyncQdrantClient | None = None
        self._url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self._api_key = os.getenv("QDRANT_API_KEY")
        self._default_collection = os.getenv("QDRANT_COLLECTION", "conv_memory")
        self._chat_id_field = os.getenv("QDRANT_CHAT_ID_FIELD", "chat_id")
        self._timestamp_field = os.getenv("QDRANT_TIMESTAMP_FIELD", "ts")
        self._verified_collections: Set[str] = set()
    
    async def _get_client(self) -> AsyncQdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            try:
                self._client = AsyncQdrantClient(
                    url=self._url,
                    api_key=self._api_key,
                    timeout=30.0
                )
                logger.info(text_loader.get_text("log.qdrant.client_connected", 
                                          url=self._url))
            except Exception as e:
                logger.error(text_loader.get_error("err.qdrant.connection", 
                                           error=str(e)))
                raise
        return self._client
    
    async def ensure_collection(
        self, 
        name: Optional[str] = None, 
        dim: int = 1024, 
        distance: str = "Cosine"
    ) -> bool:
        """Ensure collection exists with proper configuration."""
        collection_name = name or self._default_collection
        
        # Use cache to avoid repeated API calls
        if collection_name in self._verified_collections:
            return True
        
        try:
            client = await self._get_client()
            
            # Try to get collection info directly (more efficient)
            try:
                await client.get_collection(collection_name)
                self._verified_collections.add(collection_name)
                return True
            except ResponseHandlingException:
                # Collection doesn't exist, create it
                pass
            
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=getattr(models.Distance, distance.upper())
                )
            )
            
            self._verified_collections.add(collection_name)
            logger.info(text_loader.get_text("log.qdrant.collection_created", 
                                      name=collection_name, dim=dim))
            return True
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.collection_setup", 
                                       error=str(e)))
            return False
    
    async def upsert_memory(
        self,
        chat_id: int,
        user_id: int,
        text: str,
        vector: List[float],
        lang: str = "fa",
        collection: Optional[str] = None
    ) -> bool:
        """Store memory vector with metadata."""
        if not vector:
            return False
        
        collection_name = collection or self._default_collection
        
        try:
            client = await self._get_client()
            
            await client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "chat_id": chat_id,
                            "user_id": user_id,
                            "text": text,
                            "lang": lang,
                            "ts": int(time.time())
                        }
                    )
                ]
            )
            
            return True
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.upsert", error=str(e)))
            return False
    
    async def search_memory(
        self,
        chat_id: int,
        query_vector: List[float],
        top_k: int = 5,
        collection: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar memories in chat context."""
        if not query_vector:
            return []
        
        try:
            client = await self._get_client()
            
            results = await client.search(
                collection_name=collection or self._default_collection,
                query_vector=query_vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=self._chat_id_field,
                            match=models.MatchValue(value=chat_id)
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True
            )
            
            return [
                SearchResult(
                    payload=EmbeddingPayload(**result.payload),
                    score=result.score,
                    id=str(result.id)
                )
                for result in results if result.payload
            ]
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.search", error=str(e)))
            return []
    
    async def compact(
        self, 
        days_keep: int = 90, 
        collection: Optional[str] = None
    ) -> int:
        """Remove old memories beyond retention period."""
        try:
            client = await self._get_client()
            cutoff_ts = int(time.time()) - (days_keep * 86400)  # 24*3600 = 86400
            
            await client.delete(
                collection_name=collection or self._default_collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=self._timestamp_field,
                                range=models.Range(lt=cutoff_ts)
                            )
                        ]
                    )
                )
            )
            
            logger.info(text_loader.get_text("log.qdrant.compact_complete"))
            return 1  # Operation completed
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.compact", error=str(e)))
            return 0
    
    async def search(
        self,
        vector: List[float],
        filter_dict: dict,
        top_k: int = 5,
        ef: Optional[int] = None
    ) -> List[dict]:
        """Search with custom filter dictionary."""
        if not vector:
            return []
        
        try:
            client = await self._get_client()
            
            # Convert filter_dict to Qdrant filter
            must_conditions = []
            for key, value in filter_dict.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            
            results = await client.search(
                collection_name=self._default_collection,
                query_vector=vector,
                query_filter=models.Filter(must=must_conditions) if must_conditions else None,
                limit=top_k,
                with_payload=True
            )
            
            return [
                {
                    "payload": result.payload,
                    "score": result.score,
                    "id": str(result.id)
                }
                for result in results if result.payload
            ]
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.search", error=str(e)))
            return []
    
    async def upsert_points(self, points: List[dict]) -> bool:
        """Upsert multiple points."""
        if not points:
            return True
        
        try:
            client = await self._get_client()
            
            point_structs = []
            for point in points:
                point_structs.append(
                    models.PointStruct(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point["payload"]
                    )
                )
            
            await client.upsert(
                collection_name=self._default_collection,
                points=point_structs
            )
            
            return True
            
        except Exception as e:
            logger.error(text_loader.get_error("err.qdrant.upsert", error=str(e)))
            return False
    
    async def healthcheck(self) -> dict:
        """Check Qdrant health."""
        try:
            client = await self._get_client()
            info = await client.get_collections()
            return {"status": "healthy", "collections": len(info.collections)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self) -> None:
        """Close Qdrant client connection."""
        if self._client:
            await self._client.close()
            self._client = None


qdrant_client = VectorMemoryDB()