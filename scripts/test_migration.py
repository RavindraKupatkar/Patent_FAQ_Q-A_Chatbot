#!/usr/bin/env python3
"""
Test script for the migration utility.
This script demonstrates the migration utility functionality without requiring actual Pinecone credentials.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.migrate_to_pinecone import MigrationUtility


def test_dry_run():
    """Test the migration utility in dry run mode."""
    print("=" * 60)
    print("Testing Migration Utility - Dry Run Mode")
    print("=" * 60)
    
    # Test with dry run mode (doesn't require Pinecone credentials)
    migrator = MigrationUtility(source_dir="vector_db", dry_run=True)
    
    print("\n1. Testing local store analysis...")
    analysis = migrator.analyze_local_store()
    
    print(f"\n2. Analysis Results:")
    for key, value in analysis.items():
        print(f"   {key}: {value}")
    
    if analysis["total_size_mb"] > 0:
        print("\n3. Testing document loading...")
        documents = migrator.load_all_documents()
        print(f"   Loaded {len(documents)} documents")
        
        if documents:
            print(f"   Sample document content: {documents[0]['page_content'][:100]}...")
            print(f"   Sample document metadata: {documents[0]['metadata']}")
            
            print("\n4. Testing re-embedding (first 3 documents)...")
            sample_docs = documents[:3]
            re_embedded = migrator.re_embed_documents(sample_docs)
            print(f"   Re-embedded {len(re_embedded)} documents")
            
            if re_embedded:
                print(f"   Embedding dimension: {len(re_embedded[0]['embedding'])}")
                print(f"   Embedding preview: {re_embedded[0]['embedding'][:5]}...")
    
    print("\n5. Running full migration test...")
    success = migrator.migrate(namespace="test", verify=False)
    
    print(f"\nMigration test completed: {'SUCCESS' if success else 'FAILED'}")
    
    return success


def test_import():
    """Test that all modules can be imported successfully."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    try:
        from scripts.migrate_to_pinecone import MigrationUtility
        print("✓ MigrationUtility imported successfully")
        
        from utils.embedder import get_embedder
        print("✓ EmbedderManager imported successfully")
        
        # Test embedder initialization
        embedder = get_embedder()
        provider_info = embedder.get_provider_info()
        print(f"✓ Embedder initialized: {provider_info['provider']} (dim: {provider_info['dimension']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🧪 Migration Utility Test Suite")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📁 Vector DB directory exists: {Path('vector_db').exists()}")
    print()
    
    # Test 1: Module imports
    import_success = test_import()
    
    print("\n" + "=" * 60)
    
    # Test 2: Dry run functionality
    if import_success:
        dry_run_success = test_dry_run()
    else:
        print("Skipping dry run test due to import failures")
        dry_run_success = False
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Module imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"Dry run test:   {'✅ PASS' if dry_run_success else '❌ FAIL'}")
    
    if import_success and dry_run_success:
        print("\n🎉 All tests passed! The migration utility is ready to use.")
        print("\nTo run actual migration:")
        print("1. Set up your .env file with Pinecone credentials")
        print("2. Run: python scripts/migrate_to_pinecone.py --source vector_db --namespace default")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
    
    return import_success and dry_run_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
