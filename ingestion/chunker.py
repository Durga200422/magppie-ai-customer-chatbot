from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib

def chunk_text(text: str, source: str) -> list[Document]:
    """
    Splits text into chunks of size 600 with an overlap of 100.
    Returns a list of LangChain Document objects with metadata.
    
    Args:
        text (str): The raw text to split.
        source (str): The source of the text (e.g., 'pdf', 'website').
    """
    if not text.strip():
        return []
        
    # Initialize the RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # Split the text into smaller string chunks
    string_chunks = text_splitter.split_text(text)
    
    documents = []
    for i, chunk in enumerate(string_chunks):
        # Create a unique ID for each chunk based on source and index
        chunk_id = f"{source}_chunk_{i}"
        
        # Create the LangChain Document
        doc = Document(
            page_content=chunk,
            metadata={
                "source": source,
                "chunk_id": chunk_id,
                "chunk_index": i
            }
        )
        documents.append(doc)
        
    print(f"Successfully created {len(documents)} chunks for source: {source}")
    return documents

if __name__ == "__main__":
    # Quick standalone test
    sample = "Magppie makes wellness kitchens. " * 40
    docs = chunk_text(sample, "test_source")
    if docs:
        print(f"First chunk content: {docs[0].page_content[:50]}...")
