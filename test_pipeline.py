import os
import sys

# Add the project root to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.chunker import chunk_text
from rag.embedder import get_embedding_model

def test_pipeline():
    print("--- Testing Chunker ---")
    sample_text = (
        "Magppie is redefining the modern kitchen by creating the world's first "
        "wellness kitchen made entirely of stone, free from toxic formaldehyde. "
    ) * 20  # Repeat to create enough text for chunking
    
    docs = chunk_text(sample_text, source="website")
    print(f"Number of chunks created: {len(docs)}")
    
    print("\n--- Testing Embedder ---")
    embedder = get_embedding_model()
    
    if docs:
        # Test embedding a single chunk
        sample_chunk = docs[0].page_content
        print("Embedding the first chunk...")
        vector = embedder.embed_query(sample_chunk)
        print(f"Dimension of embedding vectors: {len(vector)}")

if __name__ == "__main__":
    test_pipeline()
