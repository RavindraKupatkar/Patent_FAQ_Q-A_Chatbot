#!/usr/bin/env python3
"""
Unit tests for services/response_generator.py

Tests the ResponseGenerator class functionality including:
- Initialization with Groq API
- Response generation with context retrieval
- Configuration management
- Error handling
- Source attribution
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from services.response_generator import ResponseGenerator


class TestResponseGenerator:
    """Test cases for ResponseGenerator class."""
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_init_success(self, mock_groq):
        """Test successful initialization of ResponseGenerator."""
        mock_client = Mock()
        mock_groq.return_value = mock_client
        mock_db_manager = Mock()
        
        response_gen = ResponseGenerator(mock_db_manager)
        
        assert response_gen.db_manager == mock_db_manager
        assert response_gen.temperature == 0.7
        assert response_gen.max_tokens == 500
        assert response_gen.model == "deepseek-r1-distill-llama-70b"
        assert response_gen.client == mock_client
        mock_groq.assert_called_once_with(api_key='test-groq-key')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_api_key(self):
        """Test initialization fails when API key is missing."""
        mock_db_manager = Mock()
        
        with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
            ResponseGenerator(mock_db_manager)
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_init_custom_parameters(self, mock_groq):
        """Test initialization with custom parameters."""
        mock_groq.return_value = Mock()
        mock_db_manager = Mock()
        
        response_gen = ResponseGenerator(
            mock_db_manager,
            temperature=0.5,
            max_tokens=300,
            model="custom-model"
        )
        
        assert response_gen.temperature == 0.5
        assert response_gen.max_tokens == 300
        assert response_gen.model == "custom-model"
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_update_config(self, mock_groq):
        """Test configuration update."""
        mock_groq.return_value = Mock()
        mock_db_manager = Mock()
        response_gen = ResponseGenerator(mock_db_manager)
        
        response_gen.update_config(temperature=0.3, max_tokens=200, model="new-model")
        
        assert response_gen.temperature == 0.3
        assert response_gen.max_tokens == 200
        assert response_gen.model == "new-model"
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_update_config_partial(self, mock_groq):
        """Test partial configuration update."""
        mock_groq.return_value = Mock()
        mock_db_manager = Mock()
        response_gen = ResponseGenerator(mock_db_manager)
        
        original_max_tokens = response_gen.max_tokens
        original_model = response_gen.model
        
        response_gen.update_config(temperature=0.9)  # Only update temperature
        
        assert response_gen.temperature == 0.9
        assert response_gen.max_tokens == original_max_tokens
        assert response_gen.model == original_model
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_get_config(self, mock_groq):
        """Test getting current configuration."""
        mock_groq.return_value = Mock()
        mock_db_manager = Mock()
        response_gen = ResponseGenerator(mock_db_manager, temperature=0.8, max_tokens=400)
        
        config = response_gen.get_config()
        
        assert config == {
            "temperature": 0.8,
            "max_tokens": 400,
            "model": "deepseek-r1-distill-llama-70b"
        }
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_with_patent_and_bis_results(self, mock_groq):
        """Test response generation with both patent and BIS search results."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Generated response with context"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        
        # Mock patent results
        patent_doc = Mock()
        patent_doc.page_content = "Patent information content"
        patent_doc.metadata = {'source': 'patent_doc.pdf'}
        
        # Mock BIS results
        bis_doc = Mock()
        bis_doc.page_content = "BIS standards content"
        bis_doc.metadata = {'source': 'bis_doc.pdf'}
        
        mock_db_manager.search.side_effect = [
            [patent_doc],  # Patent results
            [bis_doc]      # BIS results
        ]
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("test query")
        
        # Verify searches were made
        assert mock_db_manager.search.call_count == 2
        mock_db_manager.search.assert_any_call("patent_faqs", "test query", limit=2)
        mock_db_manager.search.assert_any_call("bis_faqs", "test query", limit=2)
        
        # Verify Groq API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        assert call_args[1]['model'] == "deepseek-r1-distill-llama-70b"
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 500
        
        # Verify context was included
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert "Patent Information:" in messages[1]['content']
        assert "BIS Information:" in messages[1]['content']
        assert "Patent information content" in messages[1]['content']
        assert "BIS standards content" in messages[1]['content']
        
        # Verify result
        assert result['answer'] == "Generated response with context"
        assert result['source'] == 'patent_doc.pdf'
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_patent_only(self, mock_groq):
        """Test response generation with only patent results."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Patent-only response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        
        patent_doc = Mock()
        patent_doc.page_content = "Patent content only"
        patent_doc.metadata = {'source': 'patent.pdf'}
        
        mock_db_manager.search.side_effect = [
            [patent_doc],  # Patent results
            []             # No BIS results
        ]
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("patent query")
        
        # Verify result
        assert result['answer'] == "Patent-only response"
        assert result['source'] == 'patent.pdf'
        
        # Verify context contains only patent information
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert "Patent Information:" in messages[1]['content']
        assert "BIS Information:" not in messages[1]['content']
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_bis_only(self, mock_groq):
        """Test response generation with only BIS results."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "BIS-only response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        
        bis_doc = Mock()
        bis_doc.page_content = "BIS content only"
        bis_doc.metadata = {'source': 'bis.pdf'}
        
        mock_db_manager.search.side_effect = [
            [],            # No patent results
            [bis_doc]      # BIS results
        ]
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("BIS query")
        
        # Verify result
        assert result['answer'] == "BIS-only response"
        assert result['source'] == 'bis.pdf'
        
        # Verify context contains only BIS information
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert "Patent Information:" not in messages[1]['content']
        assert "BIS Information:" in messages[1]['content']
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_no_results(self, mock_groq):
        """Test response generation with no search results."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "No context response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        mock_db_manager.search.return_value = []  # No results from either search
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("unknown query")
        
        # Verify result
        assert result['answer'] == "No context response"
        assert result['source'] is None
        
        # Verify empty context was sent
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        context_content = messages[1]['content']
        assert "Context:\n\n" in context_content  # Empty context
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_with_custom_parameters(self, mock_groq):
        """Test response generation with custom temperature and max_tokens."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Custom params response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        mock_db_manager.search.return_value = []
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response(
            "test query",
            temperature=0.2,
            max_tokens=100
        )
        
        # Verify custom parameters were used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.2
        assert call_args[1]['max_tokens'] == 100
        
        assert result['answer'] == "Custom params response"
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_groq_error(self, mock_groq):
        """Test response generation handles Groq API errors gracefully."""
        # Setup mocks
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Groq API Error")
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        mock_db_manager.search.return_value = []
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("test query")
        
        # Verify error handling
        assert "I apologize, but I encountered an error" in result['answer']
        assert result['source'] is None
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_db_error(self, mock_groq):
        """Test response generation handles database search errors."""
        mock_client = Mock()
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        mock_db_manager.search.side_effect = Exception("DB Error")
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("test query")
        
        # Verify error handling
        assert "I apologize, but I encountered an error" in result['answer']
        assert result['source'] is None
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_generate_response_strips_whitespace(self, mock_groq):
        """Test that response content is properly stripped of whitespace."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "  \n  Response with whitespace  \n  "
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        mock_db_manager.search.return_value = []
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("test query")
        
        # Verify whitespace was stripped
        assert result['answer'] == "Response with whitespace"
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-groq-key'})
    @patch('services.response_generator.Groq')
    def test_multiple_documents_context_formatting(self, mock_groq):
        """Test proper formatting when multiple documents are returned."""
        # Setup mocks
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Multi-doc response"
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client
        
        mock_db_manager = Mock()
        
        # Multiple patent docs
        patent_docs = []
        for i in range(2):
            doc = Mock()
            doc.page_content = f"Patent content {i+1}"
            doc.metadata = {'source': f'patent{i+1}.pdf'}
            patent_docs.append(doc)
        
        # Multiple BIS docs
        bis_docs = []
        for i in range(2):
            doc = Mock()
            doc.page_content = f"BIS content {i+1}"
            doc.metadata = {'source': f'bis{i+1}.pdf'}
            bis_docs.append(doc)
        
        mock_db_manager.search.side_effect = [patent_docs, bis_docs]
        
        response_gen = ResponseGenerator(mock_db_manager)
        result = response_gen.generate_response("multi-doc query")
        
        # Verify context formatting
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        context_content = messages[1]['content']
        
        # Should contain all document contents
        assert "Patent content 1" in context_content
        assert "Patent content 2" in context_content
        assert "BIS content 1" in context_content
        assert "BIS content 2" in context_content
        
        # Source should be from first patent document
        assert result['source'] == 'patent1.pdf'


if __name__ == "__main__":
    # Run tests with: python -m pytest test_response_generator.py -v
    pytest.main([__file__, "-v"])
