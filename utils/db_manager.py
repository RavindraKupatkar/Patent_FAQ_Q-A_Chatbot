"""
Vector Database Manager - Pinecone Implementation

Refactored to use Pinecone for cloud-based vector storage with automatic index creation.
Provides backward compatibility with the original interface while leveraging:
- Pinecone client for vector storage and retrieval
- Open-source embeddings (sentence-transformers with Groq/open-source fallback)
- Automatic index creation for Streamlit Cloud deployments
- Namespace-based collections for organizing documents

Required environment variables:
- PINECONE_API_KEY: Your Pinecone API key
- PINECONE_ENV: Pinecone environment (e.g., us-east-1-aws)
- PINECONE_INDEX_NAME: Name of the Pinecone index
- GROQ_API_KEY: Groq API key for embeddings (optional, falls back to sentence-transformers)
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import streamlit as st
from pinecone import Pinecone, ServerlessSpec
import time
from .embedder import get_embedder

load_dotenv()

class VectorDBManager:
    def __init__(self):
        # Initialize embedder for generating embeddings
        self.embedder = get_embedder()
        
        # Initialize Pinecone client
        pinecone_api_key = st.secrets.get("PINECONE_API_KEY", os.getenv('PINECONE_API_KEY'))
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables or Streamlit secrets")
        
        self.pc = Pinecone(api_key=pinecone_api_key)
        
        # Get index name from environment
        self.index_name = st.secrets.get("PINECONE_INDEX_NAME", os.getenv('PINECONE_INDEX_NAME'))
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME not found in environment variables or Streamlit secrets")
        
        # Initialize or connect to index with appropriate dimension
        self.index = self._initialize_index()
        self.embeddings_cache = {}
    
    def _initialize_index(self):
        """Initialize or connect to a Pinecone index."""
        try:
            # Get the dimension from the embedder
            embedding_dimension = self.embedder.get_embedding_dimension()
            
            # Check for existing indexes
            existing_indexes = [index['name'] for index in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                # Create index with correct dimension for the embedder
                print(f"Creating Pinecone index '{self.index_name}' with dimension {embedding_dimension}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=embedding_dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                # Allow some time for index creation
                time.sleep(10)  # Increase wait time for cloud deployment
            else:
                print(f"Using existing Pinecone index '{self.index_name}'")
                
            return self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Error initializing Pinecone index: {str(e)}")
            raise

    def create_collection(self, name: str):
        """Create a new collection (namespace in Pinecone)."""
        # In Pinecone, namespaces are created implicitly when data is upserted
        # We'll keep track of created namespaces for compatibility
        if not hasattr(self, '_namespaces'):
            self._namespaces = set()
        self._namespaces.add(name)

    def upsert_embeddings(self, namespace: str, documents: List[Dict[str, Any]]):
        """Upsert embeddings to the Pinecone index."""
        try:
            vectors = []
            for i, doc in enumerate(documents):
                # Get embedding
                embedding = self._get_embedding(doc['page_content'])
                if embedding:
                    # Create unique ID using namespace and chunk info
                    # Handle both Windows and Unix path separators
                    source_filename = os.path.basename(doc['metadata']['source'])
                    doc_id = f"{namespace}_{source_filename}_{doc['metadata']['chunk_id']}"
                    # Include metadata in the vector
                    vectors.append({
                        'id': doc_id,
                        'values': embedding,
                        'metadata': {
                            'page_content': doc['page_content'][:40000],  # Limit metadata size
                            'source': doc['metadata']['source'],
                            'chunk_id': str(doc['metadata']['chunk_id'])
                        }
                    })
            
            if vectors:
                # Upsert in batches for better performance
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(vectors=batch, namespace=namespace)
                    time.sleep(0.1)  # Small delay between batches
        except Exception as e:
            print(f"Error upserting embeddings: {str(e)}")
            raise

    def query_embeddings(self, namespace: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query Pinecone for documents similar to the query."""
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []
        
        try:
            results = self.index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=top_k,
                include_metadata=True
            )
            
            # Return documents in the same format as the old interface
            documents = []
            for match in results['matches']:
                documents.append({
                    'page_content': match['metadata']['page_content'],
                    'metadata': {
                        'source': match['metadata']['source'],
                        'chunk_id': match['metadata']['chunk_id']
                    },
                    'score': match['score']
                })
            return documents
        except Exception as e:
            print(f"Error querying Pinecone: {str(e)}")
            return []

    def delete_namespace(self, namespace: str):
        """Delete a namespace from the index."""
        try:
            self.index.delete(delete_all=True, namespace=namespace)
        except Exception as e:
            print(f"Error deleting namespace {namespace}: {str(e)}")
            raise
    
    def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and process a PDF file."""
        try:
            import PyPDF2
            
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    content += page.extract_text() + "\n"
            
            # Split content into chunks
            chunks = self._split_text(content)
            
            # Create documents with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                documents.append({
                    'page_content': chunk,
                    'metadata': {
                        'source': file_path,
                        'chunk_id': i
                    }
                })
            
            return documents
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            return []
    
    def _split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the new embedder."""
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            # Use the new embedder to generate embeddings
            embeddings = self.embedder.generate([text])
            if embeddings and len(embeddings) > 0:
                embedding = embeddings[0]  # Get the first (and only) embedding
                self.embeddings_cache[text] = embedding
                return embedding
            else:
                print(f"No embedding generated for text: {text[:50]}...")
                return []
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            return []
    
    def index_document(self, collection: str, documents: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Index documents in a collection (namespace in Pinecone)."""
        self.create_collection(collection)
        
        # Update documents with additional metadata if provided
        if metadata:
            for doc in documents:
                doc['metadata'].update(metadata)
        
        # Use the new upsert_embeddings method
        self.upsert_embeddings(collection, documents)
    
    def search(self, collection: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in a collection (namespace in Pinecone)."""
        # Use the new query_embeddings method
        return self.query_embeddings(collection, query, limit)
    
    # Cosine similarity no longer needed as Pinecone handles similarity computation
    
    def save(self, path: str):
        """Save method is not needed with Pinecone as data persists in cloud."""
        # With Pinecone, data is automatically persisted in the cloud
        # This method is kept for compatibility but does nothing
        pass
    
    def load(self, path: str):
        """Load method is not needed with Pinecone as data persists in cloud."""
        # With Pinecone, data is automatically available from the cloud index
        # This method is kept for compatibility but does nothing
        pass
    
    