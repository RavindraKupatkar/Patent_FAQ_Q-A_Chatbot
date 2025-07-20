# Data Migration Scripts

## migrate_to_pinecone.py

A comprehensive utility to migrate existing local vector store data to Pinecone with re-embedding support.

### Features

- **Multi-source support**: Reads from FAISS indexes, ChromaDB, and pickle files
- **Re-embedding**: Uses the new Groq + open-source embedder to ensure dimension compatibility
- **Batch processing**: Handles large datasets efficiently with batch processing
- **Dry run mode**: Analyze your data without performing migration
- **Verification**: Tests queries after migration to ensure data integrity
- **Progress tracking**: Detailed progress reporting and error handling

### Prerequisites

Ensure you have the required environment variables set in your `.env` file:

```bash
# Required for Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=us-east-1-aws  # or your Pinecone environment
PINECONE_INDEX_NAME=your_index_name

# Optional for Groq embeddings (falls back to sentence-transformers)
GROQ_API_KEY=your_groq_api_key
```

### Usage

#### Basic Migration
```bash
python scripts/migrate_to_pinecone.py --source vector_db --namespace default
```

#### Dry Run (Analyze Only)
```bash
python scripts/migrate_to_pinecone.py --source vector_db --dry-run
```

#### Migration with Custom Namespace
```bash
python scripts/migrate_to_pinecone.py --source vector_db --namespace my_documents
```

#### Migration without Verification
```bash
python scripts/migrate_to_pinecone.py --source vector_db --no-verify
```

### Command Line Options

- `--source`: Path to local vector store directory (default: `vector_db`)
- `--namespace`: Pinecone namespace for migrated data (default: `migrated`)
- `--dry-run`: Analyze data without performing migration
- `--no-verify`: Skip verification step after migration
- `--verbose`: Enable verbose output

### Migration Process

1. **Analysis**: Scans and analyzes the local vector store structure
2. **Loading**: Extracts documents from pickle files and ChromaDB
3. **Re-embedding**: Generates new embeddings using the current embedder
4. **Upserting**: Uploads data to Pinecone with unique document IDs
5. **Verification**: Tests sample queries to ensure migration success
6. **Reporting**: Provides detailed statistics and success rates

### Supported Local Store Formats

- **FAISS indexes** (`.index` files)
- **Pickle files** (`text.pkl`, `metadata.pkl`)
- **ChromaDB** (`chroma.sqlite3`)
- **Metadata files** (various formats)

### Output Example

```
🚀 Starting migration from local vector store to Pinecone...
📍 Target namespace: 'default'

🔍 Analyzing local vector store in: vector_db
📊 Local Vector Store Analysis:
   • Total size: 0.41 MB
   • FAISS indexes: 2
   • Pickle files: 2
   • ChromaDB: Yes
   • Metadata files: 1

📖 Loading documents from vector_db\text.pkl
📝 Loading metadata from vector_db\metadata.pkl
✓ Loaded 156 documents from pickle files

📊 Loading documents from ChromaDB: vector_db\chroma.sqlite3
📋 Found tables: ['embeddings', 'collections', 'segments']
✓ Loaded 0 documents from ChromaDB

📚 Found 156 unique documents (skipped 0 duplicates)

🔄 Re-embedding 156 documents with new embedder...
📐 Using embedder: sentence_transformers (dimension: 384)
🔄 Processing batch 1/4
🔄 Processing batch 2/4
🔄 Processing batch 3/4
🔄 Processing batch 4/4
✓ Successfully re-embedded 156 documents

☁️ Upserting 156 documents to Pinecone namespace 'default'...
✅ Successfully migrated 156 documents to Pinecone

🔍 Verifying migration with 5 test queries...
🔍 Testing query 1: 'artificial intelligence'
   ✓ Found 3 results
      1. Score: 0.742 - Introduction to artificial intelligence and machine learning concepts...
      2. Score: 0.681 - AI applications in business intelligence and data processing...
✅ Migration verification completed

============================================================
📊 MIGRATION SUMMARY
============================================================
Documents found:     156
Documents migrated:  156
Documents skipped:   0
Errors:              0
Success rate:        100.0%
============================================================
✅ Migration completed successfully!
```

### Error Handling

The script includes comprehensive error handling for:
- Missing environment variables
- Invalid source directories
- Corrupted data files
- Network connectivity issues
- Pinecone API errors

### Performance Notes

- Processes documents in batches of 50 for optimal memory usage
- Includes small delays between batches to avoid rate limiting
- Caches embeddings to avoid regenerating for identical content
- Removes duplicate documents based on content hashing

### Troubleshooting

If you encounter issues:

1. **Check environment variables**: Ensure all required Pinecone credentials are set
2. **Verify source data**: Run with `--dry-run` to analyze your data first  
3. **Check connectivity**: Ensure you can access Pinecone from your network
4. **Review logs**: The script provides detailed error messages and progress updates
5. **Test with smaller batches**: If memory issues occur, the batch size can be adjusted in the code

### Integration

This migration utility is designed to work seamlessly with:
- The existing `VectorDBManager` class
- The new `EmbedderManager` with Groq + open-source fallback
- Pinecone cloud vector database
- Existing document loading and processing pipelines
