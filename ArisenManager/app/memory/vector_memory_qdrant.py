import os
import time
import math
import hashlib
import asyncio
import logging
from typing import List, Dict, Optional, Any
from collections import defaultdict

from .qdrant_client import qdrant_client
from .schemas import MemoryPayload, ContextResult
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class VectorMemoryQdrant:
    def __init__(self) -> None:
        self.config = config_loader.load_yaml("vector_memory.yml")
        self._load_settings()
        
        self._batch_buffer: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        self._recent_hashes: Dict[str, float] = {}
        self._lru_cache: Dict[int, List[ContextResult]] = {}
        
        self._flush_task = None
    
    def _load_settings(self) -> None:
        """Load configuration settings with environment variable fallbacks"""
        defaults = self.config["defaults"]
        env_keys = self.config["env_keys"]
        
        self.top_k_default = int(os.getenv(env_keys["top_k"], str(defaults["top_k"])))
        self.days_back_default = int(os.getenv(env_keys["days_back"], str(defaults["days_back"])))
        self.batch_size = int(os.getenv(env_keys["batch_size"], str(defaults["batch_size"])))
        self.flush_interval_ms = int(os.getenv(env_keys["flush_interval_ms"], str(defaults["flush_interval_ms"])))
        self.time_decay_lambda = float(os.getenv(env_keys["time_decay_lambda"], str(defaults["time_decay_lambda"])))
        self.dedup_window_minutes = int(os.getenv(env_keys["dedup_window_minutes"], str(defaults["dedup_window_minutes"])))
        self._cache_size = defaults["cache_size"]
    
    async def init(self) -> bool:
        """Initialize Qdrant collection and start background tasks"""
        try:
            success = await qdrant_client.ensure_collection()
            if success and not self._flush_task:
                self._flush_task = asyncio.create_task(self._background_flush())
            return success
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.init_error", error=str(e)))
            return False
    
    def _sanitize_text(self, text: str) -> str:
        """Clean and normalize text"""
        max_length = self.config["text_processing"]["max_text_length"]
        return text.strip()[:max_length]
    
    def _generate_hash(self, group_id: int, user_id: int, text: str) -> str:
        """Generate secure hash for deduplication"""
        content = f"{group_id}:{user_id}:{text}"
        hash_config = self.config["hashing"]
        
        if hash_config["algorithm"] == "sha256":
            return hashlib.sha256(content.encode(hash_config["encoding"])).hexdigest()
        else:
            # Fallback to sha256 for security
            return hashlib.sha256(content.encode(hash_config["encoding"])).hexdigest()
    
    def _is_duplicate(self, group_id: int, user_id: int, text: str) -> bool:
        """Check if text is duplicate within dedup window"""
        try:
            text_hash = self._generate_hash(group_id, user_id, text)
            current_time = time.time()
            
            if text_hash in self._recent_hashes:
                age_minutes = (current_time - self._recent_hashes[text_hash]) / self.config["time_constants"]["minutes_per_hour"]
                if age_minutes < self.dedup_window_minutes:
                    return True
            
            self._recent_hashes[text_hash] = current_time
            
            # Cleanup old hashes
            cutoff = current_time - (self.dedup_window_minutes * self.config["time_constants"]["minutes_per_hour"])
            self._recent_hashes = {
                h: t for h, t in self._recent_hashes.items() if t > cutoff
            }
            
            return False
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.cache_error", error=str(e)))
            return False
    
    async def upsert_memory(self, group_id: int, user_id: int, user_name: str,
                           text: str, embedding: List[float], *,
                           ts: Optional[int] = None, model: Optional[str] = None,
                           lang: str = None) -> None:
        """Store conversational memory with batching"""
        try:
            text = self._sanitize_text(text)
            min_length = self.config["text_processing"]["min_text_length"]
            
            if len(text) < min_length or self._is_duplicate(group_id, user_id, text):
                return
            
            if ts is None:
                ts = int(time.time())
            
            if model is None:
                model = text_loader.get_text("vector_memory.defaults.model")
            
            if lang is None:
                lang = text_loader.get_text("vector_memory.defaults.language")
            
            # Generate point ID
            hash_suffix = hash(text) % self.config["point_generation"]["hash_modulo"]
            point_id = self.config["point_generation"]["id_template"].format(
                group_id=group_id,
                user_id=user_id,
                ts=ts,
                hash_suffix=hash_suffix
            )
            
            payload_keys = self.config["payload_keys"]
            point = {
                "id": point_id,
                "vector": embedding,
                "payload": {
                    payload_keys["group_id"]: group_id,
                    payload_keys["user_id"]: user_id,
                    payload_keys["user_name"]: user_name,
                    payload_keys["timestamp"]: ts,
                    payload_keys["text"]: text,
                    payload_keys["model"]: model,
                    payload_keys["language"]: lang
                }
            }
            
            self._batch_buffer.append(point)
            
            # Flush if buffer is full
            if len(self._batch_buffer) >= self.batch_size:
                await self._flush_batch()
                
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.upsert_error", error=str(e)))
    
    async def get_context(self, group_id: int, user_id: Optional[int] = None, *,
                         top_k: Optional[int] = None, days_back: Optional[int] = None,
                         ef: Optional[int] = None, query_vector: Optional[List[float]] = None) -> List[ContextResult]:
        """Retrieve conversational context with time decay"""
        try:
            # Use cache if no specific query vector
            cache_key = f"{group_id}_{user_id or 0}"
            if not query_vector and cache_key in self._lru_cache:
                return self._lru_cache[cache_key]
            
            if top_k is None:
                top_k = self.top_k_default
            if days_back is None:
                days_back = self.days_back_default
            if ef is None:
                ef = self.config["defaults"]["ef_search"]
            
            # Build filter
            payload_keys = self.config["payload_keys"]
            filter_dict = {payload_keys["group_id"]: group_id}
            if user_id:
                filter_dict[payload_keys["user_id"]] = user_id
            
            # Time filter
            seconds_per_day = self.config["time_constants"]["seconds_per_day"]
            cutoff_ts = int(time.time()) - (days_back * seconds_per_day)
            
            # If no query vector, return empty results (would need different implementation)
            if not query_vector:
                return []
            
            # Vector search
            search_results = await qdrant_client.search(
                vector=query_vector,
                filter_dict=filter_dict,
                top_k=top_k,
                ef=ef
            )
            
            results = []
            current_time = time.time()
            
            for result in search_results:
                payload = result.get("payload", {})
                score = result.get("score", 0.0)
                
                # Apply time decay
                ts_key = payload_keys["timestamp"]
                age_days = (current_time - payload.get(ts_key, 0)) / seconds_per_day
                decayed_score = score * math.exp(-self.time_decay_lambda * age_days)
                
                # Filter by time window
                if payload.get(ts_key, 0) < cutoff_ts:
                    continue
                
                context_result = ContextResult(
                    text=payload.get(payload_keys["text"], ""),
                    user_id=payload.get(payload_keys["user_id"], 0),
                    user_name=payload.get(payload_keys["user_name"], ""),
                    ts=payload.get(ts_key, 0),
                    score=decayed_score
                )
                results.append(context_result)
            
            # Sort by decayed score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Cache results
            if not query_vector:
                self._update_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.get_context_error", error=str(e)))
            return []
    
    def _update_cache(self, key: str, results: List[ContextResult]) -> None:
        """Update LRU cache"""
        try:
            self._lru_cache[key] = results
            
            # Keep cache size limited
            if len(self._lru_cache) > self._cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._lru_cache))
                del self._lru_cache[oldest_key]
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.cache_error", error=str(e)))
    
    async def _flush_batch(self) -> None:
        """Flush current batch to Qdrant"""
        if not self._batch_buffer:
            return
        
        try:
            success = await qdrant_client.upsert_points(self._batch_buffer)
            if success:
                logger.debug(f"Flushed {len(self._batch_buffer)} points to Qdrant")
            else:
                logger.warning(f"Failed to flush {len(self._batch_buffer)} points")
            
            self._batch_buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            logger.error(text_loader.get_error("vector_memory.flush_error", error=str(e)))
    
    async def _background_flush(self) -> None:
        """Background task to flush batches periodically"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval_ms / 1000)
                
                if (time.time() - self._last_flush) * 1000 > self.flush_interval_ms:
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(text_loader.get_error("vector_memory.background_flush_error", error=str(e)))
    
    async def healthcheck(self) -> Dict[str, Any]:
        """Check system health"""
        return await qdrant_client.healthcheck()
    
    async def close(self) -> None:
        """Cleanup resources"""
        try:
            if self._flush_task:
                self._flush_task.cancel()
            
            await self._flush_batch()  # Final flush
            await qdrant_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

vector_memory = VectorMemoryQdrant()