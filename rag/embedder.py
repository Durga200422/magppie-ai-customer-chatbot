import os
from dotenv import load_dotenv

load_dotenv()

def get_embedding_model():
    """
    Returns a LangChain-compatible embedding object using Google's
    text-embedding-004 model via the Gemini API.

    This replaces the previous sentence-transformers / PyTorch approach,
    completely eliminating the torch / torchvision dependency chain that
    caused deployment failures on Streamlit Cloud.

    Requires:  GEMINI_API_KEY (or GOOGLE_API_KEY) in environment.
    """
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    # Ensure GOOGLE_API_KEY is available (langchain-google-genai reads it)
    if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

    print("Loading Google Generative AI embedding model (gemini-embedding-001)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    print("Embedding model loaded successfully.")
    return embeddings


if __name__ == "__main__":
    embedder = get_embedding_model()
    test_vector = embedder.embed_query("Magppie wellness kitchens")
    print(f"Test vector dimension: {len(test_vector)}")
