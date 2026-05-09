import os
import sys

# Ensure stdout handles utf-8 characters properly on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from ingestion.pdf_loader import extract_text_from_pdf
from ingestion.web_scraper import crawl_and_extract
from ingestion.chunker import chunk_text
from rag.embedder import get_embedding_model
from rag.vector_store import build_vector_store

def main():
    print("=== Step 1: Data Extraction ===")
    
    # 1. Load PDF
    # We use os.path.abspath to ensure it correctly finds data/magppie.pdf from root
    pdf_path = os.path.join("data", "magppie.pdf")
    pdf_text = ""
    try:
        pdf_text, pdf_pages = extract_text_from_pdf(pdf_path)
        print(f"PDF Extraction Complete: {len(pdf_text)} characters extracted.\n")
    except Exception as e:
        print(f"Failed to load PDF: {e}\n")
        
    # 2. Scrape Website
    target_url = "https://www.magppie.com"
    web_text = ""
    try:
        web_text, web_pages = crawl_and_extract(target_url, max_pages=25)
        print(f"\nWeb Scraping Complete: {len(web_text)} characters extracted.\n")
    except Exception as e:
        print(f"Failed to scrape website: {e}\n")
        
    print("=== Step 2: Chunking ===")
    all_chunks = []
    
    if pdf_text:
        pdf_chunks = chunk_text(pdf_text, source="pdf")
        all_chunks.extend(pdf_chunks)
        
    if web_text:
        web_chunks = chunk_text(web_text, source="website")
        all_chunks.extend(web_chunks)
        
    total_chunks = len(all_chunks)
    print(f"Total chunks created: {total_chunks}")
    
    if total_chunks == 0:
        print("No content extracted. Aborting build.")
        sys.exit(1)
        
    print("\n=== Step 3: Embeddings & Vector Store ===")
    # Initialize the local CPU embedding model
    embeddings = get_embedding_model()
    
    # Build and persist the Chroma database
    build_vector_store(all_chunks, embeddings)
    
    print("\n" + "="*60)
    print(f"SUCCESS: Knowledge base successfully built and indexed {total_chunks} chunks!")
    print("="*60)

if __name__ == "__main__":
    main()
