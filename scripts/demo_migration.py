#!/usr/bin/env python3
"""
Demonstration of the Migration Utility functionality.
This script shows how the migration utility works without requiring Pinecone to be installed.
"""

import os
import sys
import pickle
import sqlite3
import json
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path to import local modules  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedder import get_embedder


class MigrationDemo:
    """Demo of the migration utility functionality."""
    
    def __init__(self, source_dir: str = "vector_db"):
        self.source_dir = Path(source_dir)
        self.embedder = get_embedder()
        self.stats = {
            "documents_found": 0,
            "documents_migrated": 0,
            "errors": 0,
            "skipped": 0
        }
    
    def analyze_local_store(self) -> Dict[str, Any]:
        """Analyze existing local vector store structure."""
        print(f"🔍 Analyzing local vector store in: {self.source_dir}")
        
        analysis = {
            "faiss_indexes": [],
            "pickle_files": [],
            "chroma_db": None,
            "metadata_files": [],
            "total_size_mb": 0
        }
        
        if not self.source_dir.exists():
            print(f"❌ Source directory {self.source_dir} does not exist")
            return analysis
        
        # Scan for different file types
        for file_path in self.source_dir.glob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                analysis["total_size_mb"] += size_mb
                
                if file_path.suffix == ".index":
                    analysis["faiss_indexes"].append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2)
                    })
                elif file_path.suffix == ".pkl":
                    analysis["pickle_files"].append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2)
                    })
                elif file_path.name == "chroma.sqlite3":
                    analysis["chroma_db"] = {
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2)
                    }
                elif "metadata" in file_path.name.lower():
                    analysis["metadata_files"].append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2)
                    })
        
        analysis["total_size_mb"] = round(analysis["total_size_mb"], 2)
        
        # Print analysis
        print(f"📊 Local Vector Store Analysis:")
        print(f"   • Total size: {analysis['total_size_mb']} MB")
        print(f"   • FAISS indexes: {len(analysis['faiss_indexes'])}")
        print(f"   • Pickle files: {len(analysis['pickle_files'])}")
        print(f"   • ChromaDB: {'Yes' if analysis['chroma_db'] else 'No'}")
        print(f"   • Metadata files: {len(analysis['metadata_files'])}")
        
        return analysis
    
    def load_documents_from_pickle(self) -> List[Dict[str, Any]]:
        """Load documents from pickle files."""
        documents = []
        
        # Try to load text.pkl and metadata.pkl
        text_pkl_path = self.source_dir / "text.pkl"
        metadata_pkl_path = self.source_dir / "metadata.pkl"
        
        if text_pkl_path.exists():
            try:
                print(f"📖 Loading documents from {text_pkl_path}")
                with open(text_pkl_path, 'rb') as f:
                    text_data = pickle.load(f)
                
                # Load metadata if available
                metadata_data = []
                if metadata_pkl_path.exists():
                    print(f"📝 Loading metadata from {metadata_pkl_path}")
                    with open(metadata_pkl_path, 'rb') as f:
                        metadata_data = pickle.load(f)
                
                # Combine text and metadata
                if isinstance(text_data, list):
                    for i, text in enumerate(text_data):
                        doc = {
                            "page_content": str(text) if text else "",
                            "metadata": {
                                "chunk_id": i,
                                "source": f"local_store_document_{i}"
                            }
                        }
                        
                        # Add metadata if available
                        if i < len(metadata_data) and isinstance(metadata_data[i], dict):
                            doc["metadata"].update(metadata_data[i])
                        
                        if doc["page_content"].strip():  # Only add non-empty documents
                            documents.append(doc)
                
                print(f"✓ Loaded {len(documents)} documents from pickle files")
                
            except Exception as e:
                print(f"❌ Error loading pickle files: {str(e)}")
        
        return documents
    
    def demonstrate_re_embedding(self, documents: List[Dict[str, Any]], sample_size: int = 3):
        """Demonstrate re-embedding with the new embedder."""
        if not documents:
            print("⚠️ No documents to re-embed")
            return []
            
        sample_docs = documents[:sample_size]
        print(f"🔄 Demonstrating re-embedding with {len(sample_docs)} sample documents...")
        
        # Get embedder info
        embedder_info = self.embedder.get_provider_info()
        print(f"📐 Using embedder: {embedder_info['provider']} (dimension: {embedder_info['dimension']})")
        
        re_embedded_docs = []
        batch_texts = [doc["page_content"] for doc in sample_docs]
        
        try:
            # Generate new embeddings
            embeddings = self.embedder.generate(batch_texts)
            
            # Add embeddings to documents
            for i, doc in enumerate(sample_docs):
                if i < len(embeddings):
                    enhanced_doc = doc.copy()
                    enhanced_doc["embedding"] = embeddings[i]
                    enhanced_doc["metadata"]["embedding_provider"] = embedder_info["provider"]
                    enhanced_doc["metadata"]["embedding_dimension"] = len(embeddings[i])
                    re_embedded_docs.append(enhanced_doc)
                    
                    # Show sample embedding
                    print(f"   Document {i+1}: Content preview: '{doc['page_content'][:80]}...'")
                    print(f"   Embedding dimension: {len(embeddings[i])}")
                    print(f"   Embedding preview: {embeddings[i][:5]}...")
                    print()
        
        except Exception as e:
            print(f"❌ Error during re-embedding: {str(e)}")
        
        print(f"✓ Successfully re-embedded {len(re_embedded_docs)} documents")
        return re_embedded_docs
    
    def demonstrate_migration_process(self):
        """Demonstrate the complete migration process."""
        print("🚀 MIGRATION UTILITY DEMONSTRATION")
        print("="*60)
        print("This demo shows how the migration utility would work:")
        print("1. Analyze local vector store")
        print("2. Load documents from local storage")
        print("3. Re-embed with new embedder")
        print("4. Show what would be uploaded to Pinecone")
        print("="*60)
        print()
        
        # Step 1: Analyze local store
        print("STEP 1: ANALYZING LOCAL VECTOR STORE")
        print("-" * 40)
        analysis = self.analyze_local_store()
        
        if analysis["total_size_mb"] == 0:
            print("❌ No data found in local vector store")
            return False
        
        print()
        
        # Step 2: Load documents
        print("STEP 2: LOADING DOCUMENTS FROM LOCAL STORAGE")
        print("-" * 40)
        documents = self.load_documents_from_pickle()
        
        if not documents:
            print("❌ No documents loaded from local store")
            return False
        
        self.stats["documents_found"] = len(documents)
        print(f"📚 Found {len(documents)} documents total")
        
        # Show sample document
        if documents:
            sample_doc = documents[0]
            print(f"\nSample document:")
            print(f"  Content: '{sample_doc['page_content'][:100]}...'")
            print(f"  Metadata: {sample_doc['metadata']}")
        
        print()
        
        # Step 3: Re-embed documents
        print("STEP 3: RE-EMBEDDING WITH NEW EMBEDDER")
        print("-" * 40)
        re_embedded_docs = self.demonstrate_re_embedding(documents, sample_size=3)
        
        if not re_embedded_docs:
            print("❌ Failed to re-embed documents")
            return False
        
        print()
        
        # Step 4: Show what would be uploaded to Pinecone
        print("STEP 4: WHAT WOULD BE UPLOADED TO PINECONE")
        print("-" * 40)
        print(f"🔥 DRY RUN: Would upload {len(documents)} documents to Pinecone")
        print(f"📍 Target namespace: 'migrated'")
        print(f"📐 Embedding dimension: {len(re_embedded_docs[0]['embedding'])}")
        print(f"🏷️ Each document would have a unique ID like: migrated_document_0")
        print()
        print("Sample document that would be uploaded:")
        sample = re_embedded_docs[0]
        print(f"  ID: migrated_{sample['metadata']['source']}_0")
        print(f"  Content: '{sample['page_content'][:80]}...'")
        print(f"  Metadata: {sample['metadata']}")
        print(f"  Embedding: [{', '.join([f'{x:.3f}' for x in sample['embedding'][:5]])}...] ({len(sample['embedding'])} dims)")
        
        print()
        
        # Step 5: Summary
        print("STEP 5: MIGRATION SUMMARY")
        print("-" * 40)
        print(f"Documents found:     {len(documents)}")
        print(f"Documents processed: {len(re_embedded_docs)}")
        print(f"Embedder used:       {self.embedder.get_provider_info()['provider']}")
        print(f"Embedding dimension: {self.embedder.get_embedding_dimension()}")
        print()
        print("✅ DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print()
        print("To run actual migration:")
        print("1. Set up your .env file with Pinecone credentials:")
        print("   PINECONE_API_KEY=your_api_key")
        print("   PINECONE_INDEX_NAME=your_index_name")
        print("2. Run: python scripts/migrate_to_pinecone.py --source vector_db --namespace default")
        
        return True


def main():
    """Main demo function."""
    print("🧪 MIGRATION UTILITY DEMONSTRATION")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📁 Vector DB directory exists: {Path('vector_db').exists()}")
    print()
    
    demo = MigrationDemo()
    success = demo.demonstrate_migration_process()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
