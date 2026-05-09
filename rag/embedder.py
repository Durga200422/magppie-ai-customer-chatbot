from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embedding_model():
    """
    Loads a local HuggingFace embedding model specifically configured to run on CPU.
    This does not use OpenAI or any paid APIs.
    
    Returns:
        HuggingFaceEmbeddings: A LangChain-compatible embedding object.
    """
    model_name = "all-MiniLM-L6-v2"
    
    # Enforce CPU usage
    model_kwargs = {'device': 'cpu'}
    # Normalizing embeddings can improve cosine similarity accuracy
    encode_kwargs = {'normalize_embeddings': True}
    
    print(f"Loading local embedding model ({model_name}) on CPU...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    
    print("Embedding model loaded successfully.")
    return embeddings

if __name__ == "__main__":
    # Quick standalone test
    embedder = get_embedding_model()
    test_vector = embedder.embed_query("Magppie wellness kitchens")
    print(f"Test vector dimension: {len(test_vector)}")
