"""Async tests for memory module."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.memory import EmbeddingService, VectorMemoryDB, EmbeddingPayload


class TestEmbeddingService:
    """Test embedding service functionality."""
    
    @pytest.fixture
    def embedding_service(self) -> EmbeddingService:
        """Create embedding service instance."""
        return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_embed_text_success(self, embedding_service: EmbeddingService) -> None:
        """Test successful text embedding."""
        mock_model = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.astype.return_value.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_embedding
        
        with patch('asyncio.to_thread') as mock_thread:
            mock_thread.side_effect = [mock_model, mock_embedding]
            
            result = await embedding_service.embed_text("test text")
            
            assert result == [0.1, 0.2, 0.3]
            assert mock_thread.call_count == 2
    
    @pytest.mark.asyncio
    async def test_embed_text_short_text(self, embedding_service: EmbeddingService) -> None:
        """Test embedding with text too short."""
        result = await embedding_service.embed_text("hi")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_embed_batch_success(self, embedding_service: EmbeddingService) -> None:
        """Test successful batch embedding."""
        mock_model = MagicMock()
        mock_embeddings = [
            MagicMock(),
            MagicMock()
        ]
        for emb in mock_embeddings:
            emb.astype.return_value.tolist.return_value = [0.1, 0.2]
        mock_model.encode.return_value = mock_embeddings
        
        with patch('asyncio.to_thread') as mock_thread:
            mock_thread.side_effect = [mock_model, mock_embeddings]
            
            result = await embedding_service.embed_batch(["text one", "text two"])
            
            assert len(result) == 2
            assert all(emb == [0.1, 0.2] for emb in result)


class TestVectorMemoryDB:
    """Test vector memory database functionality."""
    
    @pytest.fixture
    def vector_db(self) -> VectorMemoryDB:
        """Create vector database instance."""
        return VectorMemoryDB()
    
    @pytest.mark.asyncio
    async def test_upsert_memory_success(self, vector_db: VectorMemoryDB) -> None:
        """Test successful memory upsert."""
        mock_client = AsyncMock()
        mock_client.upsert = AsyncMock()
        
        with patch.object(vector_db, '_get_client', return_value=mock_client):
            result = await vector_db.upsert_memory(
                chat_id=123,
                user_id=456,
                text="test memory",
                vector=[0.1, 0.2, 0.3]
            )
            
            assert result is True
            mock_client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_memory_success(self, vector_db: VectorMemoryDB) -> None:
        """Test successful memory search."""
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.payload = {
            "chat_id": 123,
            "user_id": 456,
            "text": "test",
            "lang": "fa",
            "ts": 1234567890
        }
        mock_result.score = 0.95
        mock_result.id = "test-id"
        mock_client.search.return_value = [mock_result]
        
        with patch.object(vector_db, '_get_client', return_value=mock_client):
            results = await vector_db.search_memory(
                chat_id=123,
                query_vector=[0.1, 0.2, 0.3]
            )
            
            assert len(results) == 1
            assert results[0].score == 0.95
            assert results[0].payload.chat_id == 123
    
    @pytest.mark.asyncio
    async def test_roundtrip_integration(self) -> None:
        """Test complete embedding -> upsert -> search roundtrip."""
        embedding_service = EmbeddingService()
        vector_db = VectorMemoryDB()
        
        # Mock embedding service
        mock_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        with patch.object(embedding_service, 'embed_text', return_value=mock_vector):
            # Mock vector database
            mock_client = AsyncMock()
            mock_client.upsert = AsyncMock()
            
            mock_search_result = MagicMock()
            mock_search_result.payload = {
                "chat_id": 123,
                "user_id": 456,
                "text": "test memory text",
                "lang": "fa",
                "ts": 1234567890
            }
            mock_search_result.score = 0.98
            mock_search_result.id = "test-uuid"
            mock_client.search.return_value = [mock_search_result]
            
            with patch.object(vector_db, '_get_client', return_value=mock_client):
                # 1. Generate embedding
                vector = await embedding_service.embed_text("test memory text")
                assert vector == mock_vector
                
                # 2. Store in vector DB
                upsert_success = await vector_db.upsert_memory(
                    chat_id=123,
                    user_id=456,
                    text="test memory text",
                    vector=vector
                )
                assert upsert_success is True
                
                # 3. Search for similar memories
                search_results = await vector_db.search_memory(
                    chat_id=123,
                    query_vector=vector
                )
                
                assert len(search_results) == 1
                assert search_results[0].payload.text == "test memory text"
                assert search_results[0].score == 0.98