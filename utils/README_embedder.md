# Embedder Utility Documentation

The `utils/embedder.py` module provides a unified interface for generating text embeddings with automatic provider fallback.

## Features

- **Primary Provider**: Groq embeddings (when API key is available)
- **Fallback Provider**: Sentence-transformers with `all-MiniLM-L6-v2` model
- **Automatic Selection**: Automatically chooses the best available provider
- **Easy Swapping**: Future provider changes require only modifying this file
- **Error Handling**: Graceful fallback and comprehensive error messages
- **Caching**: Built-in singleton pattern for efficient model loading

## Quick Start

### Basic Usage

```python
from utils.embedder import generate

# Generate embeddings for multiple texts
texts = [
    "This is the first document.",
    "Here is another piece of text.",
    "And a third example."
]

embeddings = generate(texts)  # Returns List[List[float]]
print(f"Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions each")
```

### Advanced Usage

```python
from utils.embedder import get_embedder

# Get detailed information about the provider
embedder = get_embedder()
info = embedder.get_provider_info()

print(f"Using provider: {info['provider']}")
print(f"Model: {info['model']}")
print(f"Embedding dimension: {info['dimension']}")

# Generate embeddings
embeddings = embedder.generate(texts)
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# For Groq embeddings (primary option)
GROQ_API_KEY=your_groq_api_key_here
```

### Streamlit Secrets

Alternatively, configure in Streamlit secrets:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your_groq_api_key_here"
```

## Provider Details

### Groq Embeddings (Primary)
- **Status**: Placeholder (awaiting Groq embedding API availability)
- **Dimensions**: TBD (likely 1536)
- **Requirements**: Groq API key
- **Advantages**: Fast inference, cloud-based

### Sentence-Transformers (Fallback)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Requirements**: No API key needed
- **Advantages**: Works offline, open-source, reliable

## Error Handling

The embedder handles various failure scenarios:

1. **Missing API Key**: Falls back to sentence-transformers
2. **Groq Service Error**: Automatic fallback with error logging
3. **Import Errors**: Clear error messages with installation instructions
4. **Invalid Input**: Validates input and provides helpful error messages

## API Reference

### `generate(texts: List[str]) -> List[List[float]]`

Main interface function for generating embeddings.

**Parameters:**
- `texts`: List of text strings to embed

**Returns:**
- List of embedding vectors (each vector is a list of floats)

**Raises:**
- `ValueError`: If input is invalid
- `RuntimeError`: If embedding generation fails

### `get_embedder() -> EmbedderManager`

Returns the global embedder instance (singleton pattern).

### `EmbedderManager.get_provider_info() -> dict`

Returns information about the current provider:

```python
{
    "provider": "sentence_transformers",
    "dimension": 384,
    "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### `EmbedderManager.get_embedding_dimension() -> int`

Returns the dimension of embeddings produced by the current provider.

## Testing

Run the test script to verify functionality:

```bash
python test_embedder.py
```

## Integration Examples

### Replace OpenAI Embeddings

If migrating from OpenAI embeddings:

```python
# Before (OpenAI)
# embedding = openai_client.embeddings.create(model="text-embedding-ada-002", input=text)

# After (New embedder)
from utils.embedder import generate
embeddings = generate([text])  # Note: input is now a list
embedding = embeddings[0]  # Extract single embedding
```

### Batch Processing

```python
from utils.embedder import generate

def process_documents(documents):
    """Process a batch of documents and return their embeddings."""
    texts = [doc['content'] for doc in documents]
    embeddings = generate(texts)
    
    for doc, embedding in zip(documents, embeddings):
        doc['embedding'] = embedding
    
    return documents
```

## Future Provider Integration

To add a new provider (e.g., Azure OpenAI, Cohere), modify only `utils/embedder.py`:

1. Add provider detection logic in `_initialize_provider()`
2. Implement provider-specific embedding method
3. Update `get_embedding_dimension()` and `get_provider_info()`
4. Update provider selection priority

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure dependencies are installed:
   ```bash
   pip install sentence-transformers torch
   ```

2. **CUDA Issues**: If using GPU, ensure compatible PyTorch version:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Memory Issues**: For large batches, process in smaller chunks:
   ```python
   def generate_large_batch(texts, batch_size=100):
       embeddings = []
       for i in range(0, len(texts), batch_size):
           batch = texts[i:i+batch_size]
           batch_embeddings = generate(batch)
           embeddings.extend(batch_embeddings)
       return embeddings
   ```

### Performance Tips

- Use batch processing for multiple texts (more efficient than single calls)
- The sentence-transformers model is cached after first load
- Consider running on GPU for large-scale processing
- Use appropriate batch sizes to balance memory and performance

## Dependencies

Required packages (automatically handled by `requirements.txt`):

```
groq>=0.4.1
sentence-transformers>=2.2.2
python-dotenv>=1.0.1
streamlit>=1.32.0
torch>=1.9.0
numpy>=1.24.0
```
