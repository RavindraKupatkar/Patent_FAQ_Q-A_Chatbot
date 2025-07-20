#!/usr/bin/env python3
"""
Data Migration Utility - Local Vector Store to Pinecone
 
This script migrates existing local vector store data to Pinecone:
1. Reads existing local vector store (FAISS indexes, ChromaDB, pickle files)
2. Re-embeds text chunks with the new embedder to ensure dimensionality match
3. Upserts data to Pinecone by document ID

Compatible with Groq + Open-source embedding fallback architecture.

Required environment variables:
- PINECONE_API_KEY: Your Pinecone API key
- PINECONE_ENV: Pinecone environment (e.g., us-east-1-aws)  
- PINECONE_INDEX_NAME: Name of the Pinecone index
- GROQ_API_KEY: Optional, for Groq embeddings (falls back to sentence-transformers)

Usage:
    python scripts/migrate_to_pinecone.py --source vector_db --namespace default
    python scripts/migrate_to_pinecone.py --help
"""

import os
import sys
import pickle
import sqlite3
import json
import argparse
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedder import get_embedder
from dotenv import load_dotenv

# Conditional import for VectorDBManager to allow dry-run testing
try:
    from utils.db_manager import VectorDBManager
    PINECONE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Pinecone not available - {str(e)}")
    print("Only dry-run mode will be available")
    VectorDBManager = None
    PINECONE_AVAILABLE = False

load_dotenv()


class MigrationUtility:
    """Utility for migrating local vector stores to Pinecone."""
    
    def __init__(self, source_dir: str = "vector_db", dry_run: bool = False):
        """
        Initialize migration utility.
        
        Args:
            source_dir: Path to existing local vector store directory
            dry_run: If True, only analyze data without performing migration
        """
        self.source_dir = Path(source_dir)
        self.dry_run = dry_run
        self.embedder = get_embedder()
        
        if not dry_run:
            if not PINECONE_AVAILABLE:
                raise RuntimeError("Pinecone is not available, but dry_run is False. Please install Pinecone or use --dry-run")
            self.vector_db = VectorDBManager()
        
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
        
        # Try to load text.pkl which seems to contain document content
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
    
    def load_documents_from_chroma(self) -> List[Dict[str, Any]]:
        """Load documents from ChromaDB SQLite file."""
        documents = []
        chroma_path = self.source_dir / "chroma.sqlite3"
        
        if not chroma_path.exists():
            return documents
        
        try:
            print(f"📊 Loading documents from ChromaDB: {chroma_path}")
            conn = sqlite3.connect(str(chroma_path))
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📋 Found tables: {[t[0] for t in tables]}")
            
            # Try to find document content in various table structures
            # ChromaDB typically stores data in 'embeddings' or similar tables
            for table_name, in tables:
                if 'embedding' in table_name.lower() or 'document' in table_name.lower():
                    try:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        print(f"📋 Table {table_name} columns: {columns}")
                        
                        # Look for text/document content
                        text_columns = [col for col in columns if any(keyword in col.lower() 
                                      for keyword in ['document', 'text', 'content', 'page_content'])]
                        
                        if text_columns:
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
                            rows = cursor.fetchall()
                            
                            for i, row in enumerate(rows):
                                # Create document from row data
                                doc = {
                                    "page_content": "",
                                    "metadata": {
                                        "chunk_id": i,
                                        "source": f"chroma_{table_name}_{i}",
                                        "table": table_name
                                    }
                                }
                                
                                # Extract text content and metadata
                                for j, col_name in enumerate(columns):
                                    if j < len(row):
                                        if col_name.lower() in ['document', 'text', 'content', 'page_content']:
                                            doc["page_content"] = str(row[j]) if row[j] else ""
                                        else:
                                            doc["metadata"][col_name] = row[j]
                                
                                if doc["page_content"].strip():
                                    documents.append(doc)
                                    
                    except Exception as e:
                        print(f"⚠️ Error processing table {table_name}: {str(e)}")
            
            conn.close()
            print(f"✓ Loaded {len(documents)} documents from ChromaDB")
            
        except Exception as e:
            print(f"❌ Error loading ChromaDB: {str(e)}")
        
        return documents
    
    def load_all_documents(self) -> List[Dict[str, Any]]:
        """Load documents from all available sources in local vector store."""
        all_documents = []
        
        # Load from pickle files
        pickle_docs = self.load_documents_from_pickle()
        all_documents.extend(pickle_docs)
        
        # Load from ChromaDB
        chroma_docs = self.load_documents_from_chroma()
        all_documents.extend(chroma_docs)
        
        # Remove duplicates based on content
        unique_documents = []
        seen_content = set()
        
        for doc in all_documents:
            content_hash = hash(doc["page_content"][:100])  # Use first 100 chars as hash
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_documents.append(doc)
            else:
                self.stats["skipped"] += 1
        
        self.stats["documents_found"] = len(unique_documents)
        print(f"📚 Found {len(unique_documents)} unique documents (skipped {self.stats['skipped']} duplicates)")
        
        return unique_documents
    
    def re_embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Re-embed documents with the new embedder to ensure dimensionality match."""
        print(f"🔄 Re-embedding {len(documents)} documents with new embedder...")
        
        # Get embedder info
        embedder_info = self.embedder.get_provider_info()
        print(f"📐 Using embedder: {embedder_info['provider']} (dimension: {embedder_info['dimension']})")
        
        re_embedded_docs = []
        batch_size = 50  # Process in batches to avoid memory issues
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_texts = [doc["page_content"] for doc in batch]
            
            try:
                print(f"🔄 Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                
                # Generate new embeddings
                embeddings = self.embedder.generate(batch_texts)
                
                # Add embeddings to documents
                for j, doc in enumerate(batch):
                    if j < len(embeddings):
                        enhanced_doc = doc.copy()
                        enhanced_doc["embedding"] = embeddings[j]
                        enhanced_doc["metadata"]["embedding_provider"] = embedder_info["provider"]
                        enhanced_doc["metadata"]["embedding_dimension"] = len(embeddings[j])
                        re_embedded_docs.append(enhanced_doc)
                    else:
                        print(f"⚠️ Missing embedding for document {i + j}")
                        self.stats["errors"] += 1
                
                # Small delay between batches
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error in batch {i//batch_size + 1}: {str(e)}")
                self.stats["errors"] += batch_size
        
        print(f"✓ Successfully re-embedded {len(re_embedded_docs)} documents")
        return re_embedded_docs
    
    def upsert_to_pinecone(self, documents: List[Dict[str, Any]], namespace: str = "migrated"):
        """Upsert documents to Pinecone by document ID."""
        if self.dry_run:
            print(f"🔥 DRY RUN: Would upsert {len(documents)} documents to namespace '{namespace}'")
            return
        
        print(f"☁️ Upserting {len(documents)} documents to Pinecone namespace '{namespace}'...")
        
        try:
            # Create the namespace/collection
            self.vector_db.create_collection(namespace)
            
            # Convert documents to the format expected by db_manager
            formatted_docs = []
            for doc in documents:
                formatted_doc = {
                    "page_content": doc["page_content"],
                    "metadata": doc["metadata"].copy()
                }
                # Remove embedding from metadata as it's handled separately
                formatted_doc["metadata"].pop("embedding_provider", None)
                formatted_doc["metadata"].pop("embedding_dimension", None)
                formatted_docs.append(formatted_doc)
            
            # Use the existing upsert_embeddings method
            self.vector_db.upsert_embeddings(namespace, formatted_docs)
            
            self.stats["documents_migrated"] = len(formatted_docs)
            print(f"✅ Successfully migrated {len(formatted_docs)} documents to Pinecone")
            
        except Exception as e:
            print(f"❌ Error upserting to Pinecone: {str(e)}")
            self.stats["errors"] += len(documents)
            raise
    
    def verify_migration(self, namespace: str, sample_size: int = 5):
        """Verify migration by testing some queries."""
        if self.dry_run:
            print("🔥 DRY RUN: Skipping verification")
            return
        
        print(f"🔍 Verifying migration with {sample_size} test queries...")
        
        try:
            # Test with some sample queries
            test_queries = [
                "artificial intelligence",
                "machine learning", 
                "data processing",
                "business intelligence",
                "document analysis"
            ]
            
            for i, query in enumerate(test_queries[:sample_size]):
                print(f"🔍 Testing query {i+1}: '{query}'")
                results = self.vector_db.query_embeddings(namespace, query, top_k=3)
                
                if results:
                    print(f"   ✓ Found {len(results)} results")
                    for j, result in enumerate(results[:2]):  # Show top 2 results
                        preview = result['page_content'][:100].replace('\n', ' ')
                        print(f"      {j+1}. Score: {result['score']:.3f} - {preview}...")
                else:
                    print(f"   ⚠️ No results found")
                
                time.sleep(0.5)  # Small delay between queries
            
            print("✅ Migration verification completed")
            
        except Exception as e:
            print(f"❌ Error during verification: {str(e)}")
    
    def print_summary(self):
        """Print migration summary."""
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        print(f"Documents found:     {self.stats['documents_found']}")
        print(f"Documents migrated:  {self.stats['documents_migrated']}")
        print(f"Documents skipped:   {self.stats['skipped']}")
        print(f"Errors:              {self.stats['errors']}")
        
        if self.stats['documents_found'] > 0:
            success_rate = (self.stats['documents_migrated'] / self.stats['documents_found']) * 100
            print(f"Success rate:        {success_rate:.1f}%")
        
        print("="*60)
        
        if self.dry_run:
            print("🔥 This was a DRY RUN - no actual migration performed")
        elif self.stats['documents_migrated'] > 0:
            print("✅ Migration completed successfully!")
        else:
            print("❌ Migration failed or no documents found")
    
    def migrate(self, namespace: str = "migrated", verify: bool = True):
        """Perform the complete migration process."""
        print("🚀 Starting migration from local vector store to Pinecone...")
        print(f"📍 Target namespace: '{namespace}'")
        
        if self.dry_run:
            print("🔥 DRY RUN MODE - No actual changes will be made")
        
        try:
            # Step 1: Analyze local store
            analysis = self.analyze_local_store()
            
            if analysis["total_size_mb"] == 0:
                print("❌ No data found in local vector store")
                return False
            
            # Step 2: Load documents from local store
            documents = self.load_all_documents()
            
            if not documents:
                print("❌ No documents loaded from local store")
                return False
            
            # Step 3: Re-embed documents with new embedder
            re_embedded_docs = self.re_embed_documents(documents)
            
            if not re_embedded_docs:
                print("❌ Failed to re-embed documents")
                return False
            
            # Step 4: Upsert to Pinecone
            self.upsert_to_pinecone(re_embedded_docs, namespace)
            
            # Step 5: Verify migration
            if verify and not self.dry_run:
                self.verify_migration(namespace)
            
            # Step 6: Print summary
            self.print_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed with error: {str(e)}")
            self.stats["errors"] += 1
            self.print_summary()
            return False


def main():
    """Main entry point for the migration utility."""
    parser = argparse.ArgumentParser(
        description="Migrate local vector store to Pinecone with re-embedding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python scripts/migrate_to_pinecone.py --source vector_db --namespace default
  
  # Dry run to analyze data without migrating
  python scripts/migrate_to_pinecone.py --source vector_db --dry-run
  
  # Migration without verification  
  python scripts/migrate_to_pinecone.py --source vector_db --no-verify
        """
    )
    
    parser.add_argument(
        "--source",
        default="vector_db",
        help="Path to local vector store directory (default: vector_db)"
    )
    
    parser.add_argument(
        "--namespace",
        default="migrated",
        help="Pinecone namespace for migrated data (default: migrated)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze data without performing migration"
    )
    
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification step after migration"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Check required environment variables
    if not args.dry_run:
        required_vars = ["PINECONE_API_KEY", "PINECONE_ENV", "PINECONE_INDEX_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these in your .env file or environment")
            return 1
    
    # Create and run migration utility
    migrator = MigrationUtility(
        source_dir=args.source,
        dry_run=args.dry_run
    )
    
    success = migrator.migrate(
        namespace=args.namespace,
        verify=not args.no_verify
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
