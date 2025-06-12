import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import pickle
from typing import List, Dict, Any

load_dotenv()

class VectorDBManager:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        self.collections = {}
        self.metadata_store = {}
        self.text_store = {}
        
    def create_collection(self, name: str) -> str:
        """Create a new FAISS index for the collection."""
        dimension = self.embedding_model.get_sentence_embedding_dimension()
        index = faiss.IndexFlatL2(dimension)
        self.collections[name] = index
        self.metadata_store[name] = []
        self.text_store[name] = []
        return name
    
    def index_document(self, collection_name: str, text: str, metadata: Dict[str, Any]):
        """Index document chunks into the FAISS index."""
        chunks = self.text_splitter.split_text(text)
        
        # Generate embeddings for chunks
        embeddings = self.embedding_model.encode(chunks)
        
        # Add embeddings to FAISS index
        self.collections[collection_name].add(np.array(embeddings).astype('float32'))
        
        # Store metadata and text for each chunk
        for chunk in chunks:
            self.metadata_store[collection_name].append(metadata)
            self.text_store[collection_name].append(chunk)
    
    def query(self, collection_name: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query the FAISS index for similar documents."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        
        # Search in FAISS index
        distances, indices = self.collections[collection_name].search(
            np.array(query_embedding).astype('float32'), 
            top_k
        )
        
        # Return results with metadata and text
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata_store[collection_name]):
                results.append({
                    'text': self.text_store[collection_name][idx],
                    'metadata': self.metadata_store[collection_name][idx],
                    'distance': float(distances[0][i])
                })
        
        return results
    
    def save(self, path: str = "./vector_db"):
        """Save the FAISS indices and metadata to disk."""
        os.makedirs(path, exist_ok=True)
        
        # Save FAISS indices
        for name, index in self.collections.items():
            faiss.write_index(index, os.path.join(path, f"{name}.index"))
        
        # Save metadata and text
        with open(os.path.join(path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata_store, f)
        with open(os.path.join(path, "text.pkl"), "wb") as f:
            pickle.dump(self.text_store, f)
    
    def load(self, path: str = "./vector_db"):
        """Load the FAISS indices and metadata from disk."""
        if not os.path.exists(path):
            return
        
        # Load FAISS indices
        for file in os.listdir(path):
            if file.endswith(".index"):
                name = file[:-6]  # Remove .index extension
                self.collections[name] = faiss.read_index(os.path.join(path, file))
        
        # Load metadata and text
        metadata_path = os.path.join(path, "metadata.pkl")
        text_path = os.path.join(path, "text.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, "rb") as f:
                self.metadata_store = pickle.load(f)
        if os.path.exists(text_path):
            with open(text_path, "rb") as f:
                self.text_store = pickle.load(f)
    
    