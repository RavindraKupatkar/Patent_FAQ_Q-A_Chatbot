#!/usr/bin/env python3
"""
Unit tests for utils/embedder.py

Tests the EmbedderManager class functionality including:
- Provider initialization (Groq and sentence-transformers)
- Embedding generation
- Error handling and fallbacks
- Provider information retrieval
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from utils.embedder import EmbedderManager, get_embedder, generate


class TestEmbedderManager:
    """Test cases for EmbedderManager class."""
    
    @patch.dict(os.environ, {}, clear=True)  # No API keys
    @patch('utils.embedder.SentenceTransformer')
    def test_init_sentence_transformers_only(self, mock_sentence_transformer):
        """Test initialization when only sentence-transformers is available."""
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        embedder = EmbedderManager()
        
        assert embedder.provider == "sentence_transformers"
        assert embedder.sentence_model == mock_model
        assert embedder.groq_client is None
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('utils.embedder.SentenceTransformer')
    def test_init_groq_fallback_to_sentence_transformers(self, mock_sentence_transformer):
        """Test Groq initialization that falls back to sentence-transformers."""
        # Mock sentence transformer as fallback
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        with patch('utils.embedder.EmbedderManager._test_groq_embeddings', return_value=False):
            embedder = EmbedderManager()
        
        # Should fall back to sentence transformers
        assert embedder.provider == "sentence_transformers"
        assert embedder.sentence_model == mock_model
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_providers_available(self):
        """Test initialization fails when no providers are available."""
        with patch('utils.embedder.SentenceTransformer', side_effect=ImportError("Not available")):
            with pytest.raises(ImportError, match="Neither Groq nor sentence-transformers is available"):
                EmbedderManager()
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_generate_sentence_transformers(self, mock_sentence_transformer):
        """Test embedding generation using sentence-transformers."""
        # Mock sentence transformer
        mock_model = Mock()
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_numpy_arrays = [Mock() for _ in mock_embeddings]
        for i, arr in enumerate(mock_numpy_arrays):
            arr.tolist.return_value = mock_embeddings[i]
        
        mock_model.encode.return_value = mock_numpy_arrays
        mock_sentence_transformer.return_value = mock_model
        
        embedder = EmbedderManager()
        test_texts = ["text 1", "text 2"]
        
        result = embedder.generate(test_texts)
        
        assert result == mock_embeddings
        mock_model.encode.assert_called_once_with(
            test_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_generate_empty_texts(self, mock_sentence_transformer):
        """Test embedding generation with empty text list."""
        mock_sentence_transformer.return_value = Mock()
        embedder = EmbedderManager()
        
        with pytest.raises(ValueError, match="Input texts list cannot be empty"):
            embedder.generate([])
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_generate_non_string_texts(self, mock_sentence_transformer):
        """Test embedding generation with non-string inputs."""
        mock_sentence_transformer.return_value = Mock()
        embedder = EmbedderManager()
        
        with pytest.raises(ValueError, match="All elements in texts must be strings"):
            embedder.generate(["text", 123, "more text"])
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_generate_empty_strings_filtered(self, mock_sentence_transformer):
        """Test embedding generation filters out empty strings."""
        mock_sentence_transformer.return_value = Mock()
        embedder = EmbedderManager()
        
        with pytest.raises(ValueError, match="All texts are empty after filtering"):
            embedder.generate(["", "   ", "\t"])
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_get_embedding_dimension_sentence_transformers(self, mock_sentence_transformer):
        """Test getting embedding dimension for sentence-transformers."""
        mock_sentence_transformer.return_value = Mock()
        embedder = EmbedderManager()
        
        dimension = embedder.get_embedding_dimension()
        
        assert dimension == 384  # all-MiniLM-L6-v2 dimension
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_get_provider_info(self, mock_sentence_transformer):
        """Test getting provider information."""
        mock_sentence_transformer.return_value = Mock()
        embedder = EmbedderManager()
        
        info = embedder.get_provider_info()
        
        assert info['provider'] == 'sentence_transformers'
        assert info['dimension'] == 384
        assert 'sentence-transformers/all-MiniLM-L6-v2' in info['model']
    
    def test_test_groq_embeddings(self):
        """Test Groq embedding availability check."""
        embedder = EmbedderManager.__new__(EmbedderManager)
        
        # Currently returns False as Groq embeddings are not implemented
        result = embedder._test_groq_embeddings()
        assert result is False
    
    def test_generate_groq_embeddings_not_implemented(self):
        """Test that Groq embeddings raise NotImplementedError."""
        embedder = EmbedderManager.__new__(EmbedderManager)
        
        with pytest.raises(NotImplementedError, match="Groq embeddings not yet implemented"):
            embedder._generate_groq_embeddings(["test"])
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_generate_with_progress_bar(self, mock_sentence_transformer):
        """Test embedding generation shows progress bar for large batches."""
        # Mock sentence transformer
        mock_model = Mock()
        mock_embeddings = [[0.1] * 384 for _ in range(15)]  # 15 embeddings
        mock_numpy_arrays = [Mock() for _ in mock_embeddings]
        for i, arr in enumerate(mock_numpy_arrays):
            arr.tolist.return_value = mock_embeddings[i]
        
        mock_model.encode.return_value = mock_numpy_arrays
        mock_sentence_transformer.return_value = mock_model
        
        embedder = EmbedderManager()
        test_texts = [f"text {i}" for i in range(15)]  # More than 10 texts
        
        embedder.generate(test_texts)
        
        # Verify progress bar is enabled for large batches
        mock_model.encode.assert_called_once_with(
            test_texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )


class TestModuleFunctions:
    """Test module-level convenience functions."""
    
    @patch('utils.embedder.EmbedderManager')
    def test_get_embedder_singleton(self, mock_embedder_class):
        """Test get_embedder returns singleton instance."""
        mock_instance = Mock()
        mock_embedder_class.return_value = mock_instance
        
        # Clear any existing instance
        import utils.embedder
        utils.embedder._embedder_instance = None
        
        # First call should create instance
        embedder1 = get_embedder()
        assert embedder1 == mock_instance
        assert mock_embedder_class.call_count == 1
        
        # Second call should return same instance
        embedder2 = get_embedder()
        assert embedder2 == mock_instance
        assert mock_embedder_class.call_count == 1  # No additional call
    
    @patch('utils.embedder.get_embedder')
    def test_generate_convenience_function(self, mock_get_embedder):
        """Test the generate convenience function."""
        mock_embedder = Mock()
        mock_embedder.generate.return_value = [[0.1, 0.2, 0.3]]
        mock_get_embedder.return_value = mock_embedder
        
        test_texts = ["test text"]
        result = generate(test_texts)
        
        assert result == [[0.1, 0.2, 0.3]]
        mock_get_embedder.assert_called_once()
        mock_embedder.generate.assert_called_once_with(test_texts)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('utils.embedder.SentenceTransformer')
    def test_sentence_transformer_encoding_error(self, mock_sentence_transformer):
        """Test handling of sentence transformer encoding errors."""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Encoding failed")
        mock_sentence_transformer.return_value = mock_model
        
        embedder = EmbedderManager()
        
        with pytest.raises(RuntimeError, match="Error generating sentence-transformer embeddings"):
            embedder.generate(["test text"])
    
    def test_no_provider_initialized_error(self):
        """Test error when no provider is initialized."""
        embedder = EmbedderManager.__new__(EmbedderManager)
        embedder.provider = None
        
        with pytest.raises(RuntimeError, match="No embedding provider initialized"):
            embedder.generate(["test"])
        
        with pytest.raises(RuntimeError, match="No embedding provider initialized"):
            embedder.get_embedding_dimension()


if __name__ == "__main__":
    # Run tests with: python -m pytest test_embedder.py -v
    pytest.main([__file__, "-v"])
