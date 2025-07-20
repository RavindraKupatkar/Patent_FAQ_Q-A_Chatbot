import os
import json
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class VectorDBManager:
    def __init__(self):
        # Try Streamlit secrets first, then environment variables
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))
        self.client = openai.OpenAI(api_key=api_key)
        self.collections = {}
        self.embeddings_cache = {}
    
    def create_collection(self, name: str):
        """Create a new collection."""
        if name not in self.collections:
            self.collections[name] = []
    
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
        """Get embedding for text using OpenAI API."""
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            self.embeddings_cache[text] = embedding
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {str(e)}")
            return []
    
    def index_document(self, collection: str, documents: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Index documents in a collection."""
        if collection not in self.collections:
            self.create_collection(collection)
        
        for doc in documents:
            if metadata:
                doc['metadata'].update(metadata)
            
            # Get embedding for the document
            embedding = self._get_embedding(doc['page_content'])
            if embedding:
                doc['embedding'] = embedding
                self.collections[collection].append(doc)
    
    def search(self, collection: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in a collection."""
        if collection not in self.collections:
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []
        
        # Calculate similarity scores
        results = []
        for doc in self.collections[collection]:
            if 'embedding' in doc:
                similarity = self._cosine_similarity(query_embedding, doc['embedding'])
                results.append((doc, similarity))
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in results[:limit]]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def save(self, path: str):
        """Save the database to disk."""
        os.makedirs(path, exist_ok=True)
        
        # Save collections
        for name, collection in self.collections.items():
            collection_path = os.path.join(path, f"{name}.json")
            with open(collection_path, 'w', encoding='utf-8') as f:
                json.dump(collection, f, ensure_ascii=False, indent=2)
    
    def load(self, path: str):
        """Load the database from disk."""
        if not os.path.exists(path):
            return
        
        # Load collections
        for filename in os.listdir(path):
            if filename.endswith('.json'):
                name = filename[:-5]  # Remove .json extension
                collection_path = os.path.join(path, filename)
                with open(collection_path, 'r', encoding='utf-8') as f:
                    self.collections[name] = json.load(f)
    
    