#!/usr/bin/env python3
"""
Unit tests for utils/db_manager.py

Tests the VectorDBManager class functionality including:
- Initialization and configuration
- Document processing and indexing
- Embedding generation and retrieval
- Pinecone integration
- Error handling
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock pinecone imports at module level
with patch.dict('sys.modules', {
    'pinecone': Mock(),
    'pinecone.Pinecone': Mock(),
    'pinecone.ServerlessSpec': Mock()
}):
    from utils.db_manager import VectorDBManager


class TestVectorDBManager:
    """Test cases for VectorDBManager class."""
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_init_success(self, mock_pinecone, mock_get_embedder):
        """Test successful initialization of VectorDBManager."""
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        # Mock Pinecone client and index
        mock_pc = Mock()
        mock_index = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        # Initialize VectorDBManager
        db_manager = VectorDBManager()
        
        # Assertions
        assert db_manager.embedder == mock_embedder
        assert db_manager.pc == mock_pc
        assert db_manager.index_name == 'test-index'
        assert db_manager.index == mock_index
        assert db_manager.embeddings_cache == {}
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_api_key(self):
        """Test initialization fails when API key is missing."""
        with pytest.raises(ValueError, match="PINECONE_API_KEY not found"):
            VectorDBManager()
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key'})
    def test_init_missing_index_name(self):
        """Test initialization fails when index name is missing."""
        with pytest.raises(ValueError, match="PINECONE_INDEX_NAME not found"):
            VectorDBManager()
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    @patch('time.sleep')
    def test_initialize_index_creates_new(self, mock_sleep, mock_pinecone, mock_get_embedder):
        """Test index creation when index doesn't exist."""
        # Mock embedder
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        # Mock Pinecone client
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = []  # No existing indexes
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        # Initialize VectorDBManager
        db_manager = VectorDBManager()
        
        # Verify index creation was called
        mock_pc.create_index.assert_called_once()
        mock_sleep.assert_called_once_with(10)  # Wait time for creation
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_create_collection(self, mock_pinecone, mock_get_embedder):
        """Test collection creation (namespace tracking)."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pinecone.return_value = mock_pc
        
        db_manager = VectorDBManager()
        db_manager.create_collection('test-collection')
        
        # Check namespace tracking
        assert hasattr(db_manager, '_namespaces')
        assert 'test-collection' in db_manager._namespaces
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_get_embedding_with_cache(self, mock_pinecone, mock_get_embedder):
        """Test embedding retrieval with caching."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_embedder.generate.return_value = [[0.1, 0.2, 0.3]]
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pinecone.return_value = mock_pc
        
        db_manager = VectorDBManager()
        test_text = "test text"
        
        # First call - should generate embedding
        embedding1 = db_manager._get_embedding(test_text)
        assert embedding1 == [0.1, 0.2, 0.3]
        assert mock_embedder.generate.call_count == 1
        
        # Second call - should use cache
        embedding2 = db_manager._get_embedding(test_text)
        assert embedding2 == [0.1, 0.2, 0.3]
        assert mock_embedder.generate.call_count == 1  # No additional call
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    @patch('time.sleep')
    def test_upsert_embeddings(self, mock_sleep, mock_pinecone, mock_get_embedder):
        """Test embedding upsert to Pinecone."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_embedder.generate.return_value = [[0.1, 0.2, 0.3]]
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_index = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        db_manager = VectorDBManager()
        
        # Test documents
        documents = [{
            'page_content': 'test content',
            'metadata': {'source': '/path/to/file.pdf', 'chunk_id': 0}
        }]
        
        db_manager.upsert_embeddings('test-namespace', documents)
        
        # Verify upsert was called
        mock_index.upsert.assert_called_once()
        mock_sleep.assert_called_once_with(0.1)  # Batch delay
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_query_embeddings(self, mock_pinecone, mock_get_embedder):
        """Test querying embeddings from Pinecone."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_embedder.generate.return_value = [[0.1, 0.2, 0.3]]
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_index = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        # Mock query results
        mock_index.query.return_value = {
            'matches': [{
                'metadata': {
                    'page_content': 'test result',
                    'source': 'test.pdf',
                    'chunk_id': '0'
                },
                'score': 0.95
            }]
        }
        
        db_manager = VectorDBManager()
        results = db_manager.query_embeddings('test-namespace', 'test query', top_k=5)
        
        # Verify query was called and results formatted correctly
        mock_index.query.assert_called_once_with(
            vector=[0.1, 0.2, 0.3],
            namespace='test-namespace',
            top_k=5,
            include_metadata=True
        )
        
        assert len(results) == 1
        assert results[0]['page_content'] == 'test result'
        assert results[0]['score'] == 0.95
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_delete_namespace(self, mock_pinecone, mock_get_embedder):
        """Test namespace deletion."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_index = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        db_manager = VectorDBManager()
        db_manager.delete_namespace('test-namespace')
        
        # Verify delete was called
        mock_index.delete.assert_called_once_with(delete_all=True, namespace='test-namespace')
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    @patch('builtins.open', create=True)
    @patch('utils.db_manager.PyPDF2')
    def test_load_pdf(self, mock_pypdf2, mock_open, mock_pinecone, mock_get_embedder):
        """Test PDF loading and processing."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pinecone.return_value = mock_pc
        
        # Mock PDF content
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF content here"
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        db_manager = VectorDBManager()
        documents = db_manager.load_pdf('test.pdf')
        
        # Verify PDF processing
        assert len(documents) > 0
        assert 'page_content' in documents[0]
        assert documents[0]['metadata']['source'] == 'test.pdf'
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_split_text(self, mock_pinecone, mock_get_embedder):
        """Test text splitting functionality."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pinecone.return_value = mock_pc
        
        db_manager = VectorDBManager()
        
        # Test text splitting
        long_text = " ".join(["word"] * 2000)  # Very long text
        chunks = db_manager._split_text(long_text, chunk_size=100)
        
        assert len(chunks) > 1
        for chunk in chunks[:-1]:  # All chunks except last should be close to chunk_size
            assert len(chunk) <= 150  # Allow some flexibility
    
    @patch.dict(os.environ, {'PINECONE_API_KEY': 'test-api-key', 'PINECONE_INDEX_NAME': 'test-index'})
    @patch('utils.db_manager.get_embedder')
    @patch('utils.db_manager.Pinecone')
    def test_index_document_and_search_integration(self, mock_pinecone, mock_get_embedder):
        """Test document indexing and search integration."""
        # Setup mocks
        mock_embedder = Mock()
        mock_embedder.get_embedding_dimension.return_value = 384
        mock_embedder.generate.return_value = [[0.1, 0.2, 0.3]]
        mock_get_embedder.return_value = mock_embedder
        
        mock_pc = Mock()
        mock_index = Mock()
        mock_pc.list_indexes.return_value = [{'name': 'test-index'}]
        mock_pc.Index.return_value = mock_index
        mock_pinecone.return_value = mock_pc
        
        # Mock search results
        mock_index.query.return_value = {
            'matches': [{
                'metadata': {
                    'page_content': 'indexed content',
                    'source': 'test.pdf',
                    'chunk_id': '0'
                },
                'score': 0.9
            }]
        }
        
        db_manager = VectorDBManager()
        
        # Test document indexing
        documents = [{
            'page_content': 'test content',
            'metadata': {'source': 'test.pdf', 'chunk_id': 0}
        }]
        
        db_manager.index_document('test-collection', documents)
        
        # Test search
        results = db_manager.search('test-collection', 'test query')
        
        # Verify both operations worked
        mock_index.upsert.assert_called_once()
        mock_index.query.assert_called_once()
        assert len(results) == 1
        assert results[0]['page_content'] == 'indexed content'


if __name__ == "__main__":
    # Run tests with: python -m pytest test_db_manager.py -v
    pytest.main([__file__, "-v"])
