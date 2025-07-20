"""
Embedder Utility - Groq + Open-Source Fallback Implementation

Provides a unified interface for generating embeddings with multiple backends:
- Primary: Groq embeddings API (if available and configured)
- Fallback: Open-source sentence-transformers model (all-MiniLM-L6-v2)

This abstraction allows easy swapping of embedding providers by changing only this file.

Required environment variables (for Groq option):
- GROQ_API_KEY: Your Groq API key

The sentence-transformers fallback requires no API keys and runs locally.
"""

import os
import warnings
from typing import List
import streamlit as st
from dotenv import load_dotenv

# Suppress sentence-transformers warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="sentence_transformers")

load_dotenv()


class EmbedderManager:
    """
    Unified embedder interface with Groq primary and sentence-transformers fallback.
    
    Automatically selects the best available embedding provider:
    1. Groq embeddings (if API key is available)
    2. Sentence-transformers all-MiniLM-L6-v2 (local fallback)
    """
    
    def __init__(self):
        self.provider = None
        self.groq_client = None
        self.sentence_model = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the best available embedding provider."""
        # Try Groq first (preferred option)
        groq_api_key = st.secrets.get("GROQ_API_KEY", os.getenv('GROQ_API_KEY'))
        
        if groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_api_key)
                
                # Test Groq connection with a simple embedding request
                test_result = self._test_groq_embeddings()
                if test_result:
                    self.provider = "groq"
                    print("✓ Using Groq embeddings")
                    return
                else:
                    print("⚠ Groq API key found but embeddings not available, falling back to open-source")
                    
            except ImportError:
                print("⚠ Groq package not available, falling back to open-source")
            except Exception as e:
                print(f"⚠ Error initializing Groq: {str(e)}, falling back to open-source")
        
        # Fallback to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            print("📥 Loading sentence-transformers model (all-MiniLM-L6-v2)...")
            self.sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.provider = "sentence_transformers"
            print("✓ Using sentence-transformers (local) embeddings")
            
        except ImportError:
            raise ImportError(
                "Neither Groq nor sentence-transformers is available. "
                "Please install: pip install groq sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize any embedding provider: {str(e)}")
    
    def _test_groq_embeddings(self) -> bool:
        """
        Test if Groq embeddings are available.
        Note: As of current Groq API, embeddings may not be directly available.
        This method checks for embedding capabilities.
        """
        try:
            # This is a placeholder test - Groq may not have direct embedding endpoints yet
            # In practice, you would test the actual embedding endpoint here
            # For now, we'll return False to use the fallback unless Groq adds embedding support
            return False
            
        except Exception:
            return False
    
    def _generate_groq_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Groq API.
        
        Note: This is a placeholder implementation since Groq may not have 
        direct embedding endpoints yet. When available, update this method
        to use the actual Groq embedding API.
        """
        # Placeholder for future Groq embedding API
        # Once Groq provides embedding endpoints, implement here:
        # response = self.groq_client.embeddings.create(
        #     model="groq-embedding-model-name",
        #     input=texts
        # )
        # return [embedding.embedding for embedding in response.data]
        
        raise NotImplementedError(
            "Groq embeddings not yet implemented. Using sentence-transformers fallback."
        )
    
    def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers."""
        try:
            embeddings = self.sentence_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10  # Only show progress for larger batches
            )
            # Convert numpy arrays to lists for consistency
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            raise RuntimeError(f"Error generating sentence-transformer embeddings: {str(e)}")
    
    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
            
        Raises:
            ValueError: If texts is empty or contains non-string elements
            RuntimeError: If embedding generation fails
        """
        if not texts:
            raise ValueError("Input texts list cannot be empty")
        
        if not all(isinstance(text, str) for text in texts):
            raise ValueError("All elements in texts must be strings")
        
        # Filter out empty strings
        non_empty_texts = [text for text in texts if text.strip()]
        if not non_empty_texts:
            raise ValueError("All texts are empty after filtering")
        
        try:
            if self.provider == "groq":
                return self._generate_groq_embeddings(non_empty_texts)
            elif self.provider == "sentence_transformers":
                return self._generate_sentence_transformer_embeddings(non_empty_texts)
            else:
                raise RuntimeError("No embedding provider initialized")
                
        except Exception as e:
            if self.provider == "groq":
                # If Groq fails, fall back to sentence transformers
                print(f"⚠ Groq embedding failed: {str(e)}, falling back to sentence-transformers")
                try:
                    from sentence_transformers import SentenceTransformer
                    if not self.sentence_model:
                        print("📥 Loading sentence-transformers model as fallback...")
                        self.sentence_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                        self.provider = "sentence_transformers"
                    
                    return self._generate_sentence_transformer_embeddings(non_empty_texts)
                except Exception as fallback_error:
                    raise RuntimeError(f"Both Groq and sentence-transformers failed: {str(fallback_error)}")
            else:
                raise RuntimeError(f"Embedding generation failed: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the current provider.
        
        Returns:
            Integer dimension of embedding vectors
        """
        if self.provider == "groq":
            # Return dimension based on Groq's embedding model
            # This will need to be updated when Groq embeddings are available
            return 1536  # Placeholder - update with actual Groq embedding dimensions
        elif self.provider == "sentence_transformers":
            # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            return 384
        else:
            raise RuntimeError("No embedding provider initialized")
    
    def get_provider_info(self) -> dict:
        """
        Get information about the current embedding provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.provider,
            "dimension": self.get_embedding_dimension(),
            "model": {
                "groq": "Groq Embedding Model (TBD)",
                "sentence_transformers": "sentence-transformers/all-MiniLM-L6-v2"
            }.get(self.provider, "Unknown")
        }


# Global embedder instance for easy importing
_embedder_instance = None

def get_embedder() -> EmbedderManager:
    """Get the global embedder instance (singleton pattern)."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = EmbedderManager()
    return _embedder_instance

def generate(texts: List[str]) -> List[List[float]]:
    """
    Convenience function for generating embeddings.
    
    This is the main interface function as requested in the task.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each vector is a list of floats)
    """
    embedder = get_embedder()
    return embedder.generate(texts)


# Example usage
if __name__ == "__main__":
    # Example usage and testing
    test_texts = [
        "This is a sample document about artificial intelligence.",
        "Machine learning is a subset of AI that focuses on learning from data.",
        "Natural language processing helps computers understand human language."
    ]
    
    try:
        embedder = get_embedder()
        print(f"Provider info: {embedder.get_provider_info()}")
        
        embeddings = generate(test_texts)
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Each embedding has {len(embeddings[0])} dimensions")
        print(f"First embedding (truncated): {embeddings[0][:5]}...")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
