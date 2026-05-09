import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import re

# Configure Tesseract path for Windows
# This is the standard installation path for Tesseract on Windows
tesseract_cmd_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_cmd_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

def clean_text(text: str) -> str:
    """
    Cleans the extracted text by removing extra whitespace and blank lines.
    """
    # Replace multiple blank lines with a double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    # Replace multiple spaces or tabs with a single space
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """
    Extracts normal text and applies OCR on images from the PDF.
    Returns the combined cleaned text and the total number of pages.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    combined_full_text = ""
    total_pages = len(doc)
    
    print(f"Starting extraction from {pdf_path} ({total_pages} pages)...")
    
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        
        # 1. Extract normal text
        page_text = page.get_text("text")
        
        # 2. Extract images and apply OCR
        ocr_text = ""
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            try:
                # Open the image using Pillow
                image = Image.open(io.BytesIO(image_bytes))
                
                # Apply OCR using pytesseract
                extracted_ocr = pytesseract.image_to_string(image)
                
                if extracted_ocr.strip():
                    ocr_text += "\n" + extracted_ocr.strip()
            except Exception as e:
                # If OCR fails (e.g., Tesseract not found), print a warning but continue
                print(f"Warning: OCR failed on page {page_num + 1}, image {img_index + 1}. Error: {e}")
                
        # 3. Merge normal text with OCR text
        combined_page_text = page_text + "\n" + ocr_text
        
        # 4. Clean the combined text
        cleaned_page_text = clean_text(combined_page_text)
        
        if cleaned_page_text:
            combined_full_text += f"\n\n[Page {page_num + 1}]\n{cleaned_page_text}"
            
    doc.close()
    
    # Final cleanup
    final_text = combined_full_text.strip()
    return final_text, total_pages

if __name__ == "__main__":
    import sys
    # Ensure stdout handles utf-8 characters properly on Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Define the path to the Magppie PDF
    # We use os.path.join to ensure cross-platform compatibility
    pdf_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "magppie.pdf")
    
    try:
        # Extract the text and get the total pages
        extracted_text, num_pages = extract_text_from_pdf(pdf_file_path)
        
        # Print results as requested
        print("\n--- Extraction Complete ---")
        print(f"Total pages processed: {num_pages}")
        print(f"Total characters extracted: {len(extracted_text)}")
        
        print("\n--- First 500 Characters ---")
        print(extracted_text[:500])
        
    except Exception as e:
        print(f"An error occurred: {e}")
