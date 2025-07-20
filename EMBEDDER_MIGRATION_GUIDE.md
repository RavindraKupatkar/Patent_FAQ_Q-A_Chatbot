# Embedder Migration Guide

This guide shows how to integrate the new `utils/embedder.py` into your existing codebase.

## Overview

The new embedder provides:
- **Primary**: Groq embeddings (when available)
- **Fallback**: Sentence-transformers `all-MiniLM-L6-v2`
- **Unified API**: `generate(texts: List[str]) -> List[List[float]]`

## Key Changes Required

### 1. Update Database Manager (utils/db_manager.py)

The current `VectorDBManager` uses OpenAI embeddings. Here's how to migrate:

#### Option A: Quick Integration (Recommended for immediate use)

Replace the `_get_embedding` method in `VectorDBManager`:

```python
# Add this import at the top
from .embedder import generate

# Replace the existing _get_embedding method
def _get_embedding(self, text: str) -> List[float]:
    """Get embedding for text using the new embedder utility."""
    if text in self.embeddings_cache:
        return self.embeddings_cache[text]
    
    try:
        # Use the new embedder (handles Groq/sentence-transformers automatically)
        embeddings = generate([text])  # Returns List[List[float]]
        embedding = embeddings[0]      # Extract single embedding
        
        self.embeddings_cache[text] = embedding
        return embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        return []
```

#### Option B: Full Modernization (Better long-term)

Replace both `_get_embedding` and add batch processing:

```python
# Add this import at the top
from .embedder import generate, get_embedder

# Replace _get_embedding method
def _get_embedding(self, text: str) -> List[float]:
    """Get embedding for text using the new embedder utility."""
    if text in self.embeddings_cache:
        return self.embeddings_cache[text]
    
    embeddings = self._get_embeddings([text])
    return embeddings[0] if embeddings else []

# Add new batch method
def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts (batch processing)."""
    # Check cache first
    uncached_texts = []
    uncached_indices = []
    result_embeddings = [None] * len(texts)
    
    for i, text in enumerate(texts):
        if text in self.embeddings_cache:
            result_embeddings[i] = self.embeddings_cache[text]
        else:
            uncached_texts.append(text)
            uncached_indices.append(i)
    
    # Generate embeddings for uncached texts
    if uncached_texts:
        try:
            new_embeddings = generate(uncached_texts)
            for idx, embedding in zip(uncached_indices, new_embeddings):
                result_embeddings[idx] = embedding
                self.embeddings_cache[texts[idx]] = embedding
        except Exception as e:
            print(f"Error getting embeddings: {str(e)}")
            # Fill with empty lists for failed embeddings
            for idx in uncached_indices:
                result_embeddings[idx] = []
    
    return result_embeddings

# Update upsert_embeddings method for batch processing
def upsert_embeddings(self, namespace: str, documents: List[Dict[str, Any]]):
    """Upsert embeddings to the Pinecone index (with batch embedding generation)."""
    try:
        # Extract texts for batch embedding generation
        texts = [doc['page_content'] for doc in documents]
        embeddings = self._get_embeddings(texts)
        
        vectors = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            if embedding:  # Only process if embedding was generated successfully
                source_filename = os.path.basename(doc['metadata']['source'])
                doc_id = f"{namespace}_{source_filename}_{doc['metadata']['chunk_id']}"
                vectors.append({
                    'id': doc_id,
                    'values': embedding,
                    'metadata': {
                        'page_content': doc['page_content'][:40000],
                        'source': doc['metadata']['source'],
                        'chunk_id': str(doc['metadata']['chunk_id'])
                    }
                })
        
        if vectors:
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                time.sleep(0.1)
    except Exception as e:
        print(f"Error upserting embeddings: {str(e)}")
        raise
```

### 2. Handle Embedding Dimension Changes

The new embedder may produce different dimensions:
- Groq embeddings: 1536 dimensions (when available)  
- Sentence-transformers: 384 dimensions

#### Update Pinecone Index Creation

In `_initialize_index()` method, make dimension dynamic:

```python
def _initialize_index(self):
    """Initialize or connect to a Pinecone index."""
    try:
        # Get embedding dimension from the embedder
        from .embedder import get_embedder
        embedder = get_embedder()
        embedding_dimension = embedder.get_embedding_dimension()
        
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=embedding_dimension,  # Dynamic dimension
                metric='cosine'
            )
            time.sleep(5)
        return pinecone.Index(self.index_name)
    except Exception as e:
        print(f"Error initializing Pinecone index: {str(e)}")
        raise
```

### 3. Remove OpenAI Dependencies

After migration, you can remove OpenAI-related code:

```python
# Remove these imports
# import openai

# Remove from __init__ method
# openai_api_key = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))
# self.openai_client = openai.OpenAI(api_key=openai_api_key)
```

### 4. Update Environment Variables

Update `.env.example` to reflect new requirements:

```bash
# Remove (no longer needed)
# OPENAI_API_KEY=your_openai_api_key_here

# Add (optional - for Groq embeddings)
GROQ_API_KEY=your_groq_api_key_here

# Keep existing Pinecone variables
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENV=your_pinecone_environment_here
PINECONE_INDEX_NAME=your_pinecone_index_name_here
```

### 5. Update Requirements (Already Done)

The `requirements.txt` already includes the necessary packages:
- `groq>=0.4.1`
- `sentence-transformers>=2.2.2`

## Testing the Migration

### 1. Basic Functionality Test

```python
# Test the new embedder directly
from utils.embedder import generate, get_embedder

# Check what provider is being used
embedder = get_embedder()
print(f"Using provider: {embedder.get_provider_info()}")

# Test embedding generation
texts = ["Test document", "Another test"]
embeddings = generate(texts)
print(f"Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions each")
```

### 2. Integration Test

```python
# Test the updated database manager
from utils.db_manager import VectorDBManager

db = VectorDBManager()

# Test document processing
sample_docs = [
    {
        'page_content': 'This is a test document.',
        'metadata': {'source': 'test.txt', 'chunk_id': 0}
    }
]

# This should now use the new embedder
db.upsert_embeddings('test_namespace', sample_docs)
results = db.query_embeddings('test_namespace', 'test query')
print(f"Retrieved {len(results)} results")
```

## Rollback Plan

If you need to rollback to OpenAI embeddings:

1. Restore the original `_get_embedding` method
2. Reinstall OpenAI: `pip install openai`
3. Restore OpenAI initialization in `__init__`
4. Update environment variables

## Performance Considerations

### Batch Processing Benefits

The new embedder supports batch processing, which is more efficient:

```python
# Old way (multiple API calls)
embeddings = [self._get_embedding(text) for text in texts]

# New way (single batch call)
embeddings = generate(texts)
```

### Provider Selection

- **Groq**: Fast cloud inference (when available)
- **Sentence-transformers**: No API costs, works offline, 384-dimensional embeddings

### Memory Usage

Sentence-transformers loads the model into memory (~90MB for all-MiniLM-L6-v2). Consider:
- Use GPU if available for better performance
- Model is cached after first load
- Consider model quantization for production

## Troubleshooting

### Common Issues

1. **Dimension Mismatch**: If migrating existing data, you may need to recreate the Pinecone index with new dimensions.

2. **Missing Dependencies**: Ensure all packages are installed:
   ```bash
   pip install sentence-transformers torch
   ```

3. **Performance**: If sentence-transformers is slow:
   ```bash
   # Install with GPU support
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Validation Steps

1. ✅ Import works: `from utils.embedder import generate`
2. ✅ Provider detected: Check `get_embedder().get_provider_info()`
3. ✅ Embeddings generated: `generate(["test"])` returns expected shape
4. ✅ Database integration: `VectorDBManager` works with new embedder
5. ✅ End-to-end: Document indexing and search work correctly

## Benefits of Migration

1. **Provider Flexibility**: Easy to switch between embedding providers
2. **Cost Optimization**: Sentence-transformers has no API costs
3. **Offline Capability**: Works without internet connection
4. **Future-Proof**: Easy to add new providers (Azure OpenAI, Cohere, etc.)
5. **Better Performance**: Batch processing support
6. **User Preference Alignment**: Uses Groq (preferred) with open-source fallback

The migration provides a more robust and flexible embedding solution while maintaining compatibility with your existing Pinecone-based vector storage system.
