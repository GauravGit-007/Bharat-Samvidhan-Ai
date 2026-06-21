import fitz  # PyMuPDF
from typing import List, Dict
import os
from src.config.settings import settings

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    def extract_text(self) -> str:
        """Extracts all text from the PDF."""
        doc = fitz.open(self.pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text

    def extract_pages(self) -> List[Dict]:
        """Extracts text page by page with metadata."""
        doc = fitz.open(self.pdf_path)
        pages = []
        for i, page in enumerate(doc):
            pages.append({
                "page_no": i + 1,
                "text": page.get_text()
            })
        doc.close()
        return pages

if __name__ == "__main__":
    # Test extraction
    parser = PDFParser(settings.RAW_DATA_PATH)
    text = parser.extract_text()
    print(f"Extracted {len(text)} characters from {settings.RAW_DATA_PATH}")
    with open(os.path.join(settings.PROCESSED_DATA_PATH, "raw_text.txt"), "w", encoding="utf-8") as f:
        f.write(text)
