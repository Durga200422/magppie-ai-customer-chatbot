import os
import shutil
from langchain_community.vectorstores import Chroma

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "magppie_knowledge"

def build_vector_store(documents, embeddings):
    """
    Builds a new Chroma vector store from documents in batches of 50.
    Ensures a clean rebuild by deleting existing database first.
    """
    if os.path.exists(CHROMA_PATH):
        print("Clearing existing vector store to ensure a clean rebuild...")
        shutil.rmtree(CHROMA_PATH)
        
    print(f"Initializing new Chroma vector store at {CHROMA_PATH}...")
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    batch_size = 50
    total_chunks = len(documents)
    print(f"Adding {total_chunks} chunks in batches of {batch_size}...")
    
    for i in range(0, total_chunks, batch_size):
        batch = documents[i:i + batch_size]
        vector_store.add_documents(batch)
        processed = min(i + batch_size, total_chunks)
        if processed % 100 == 0 or processed == total_chunks:
            print(f"  Progress: {processed}/{total_chunks} chunks stored...")
            
    if hasattr(vector_store, 'persist'):
        vector_store.persist()
        
    print(f"Vector store successfully built with {total_chunks} total chunks.")
    return vector_store


def load_vector_store(embeddings):
    """
    Loads an existing Chroma vector store from the local directory.
    Raises FileNotFoundError if it does not exist.
    """
    if not os.path.exists(CHROMA_PATH):
        raise FileNotFoundError(
            f"Vector store directory '{CHROMA_PATH}' does not exist. Please build it first."
        )
        
    print(f"Loading existing vector store from {CHROMA_PATH}...")
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    try:
        count = vector_store._collection.count()
        print(f"Successfully loaded vector store with {count} documents.")
    except Exception:
        print("Successfully loaded vector store.")
        
    return vector_store


def load_or_build_vector_store(embeddings):
    """
    Deployment-safe loader: loads the existing vector store if present,
    otherwise triggers a full build from PDF + web sources.

    This ensures the chatbot works on Streamlit Cloud where the filesystem
    starts empty on every new deployment.
    """
    if os.path.exists(CHROMA_PATH):
        return load_vector_store(embeddings)

    print("[STARTUP] chroma_db not found — building knowledge base automatically...")
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        import sys
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from build_knowledge_base import main as build_main
        build_main()
        print("[STARTUP] Knowledge base build complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to auto-build knowledge base: {e}")

    return load_vector_store(embeddings)
