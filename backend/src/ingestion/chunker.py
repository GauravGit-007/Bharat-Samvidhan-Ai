import re
import json
import os
from typing import List, Dict
from src.config.settings import settings

class ArticleChunker:
    def __init__(self, raw_text_path: str):
        self.raw_text_path = raw_text_path
        if not os.path.exists(raw_text_path):
            raise FileNotFoundError(f"Raw text file not found at {raw_text_path}")

    def load_text(self) -> str:
        with open(self.raw_text_path, "r", encoding="utf-8") as f:
            return f.read()

    def chunk_by_article(self) -> List[Dict]:
        text = self.load_text()
        
        # Split by Part headers first to get more context
        parts = re.split(r"(PART\s+[IVXLCD]+)", text)
        
        chunks = []
        current_part = "Preamble"
        idx = 0
        
        for i in range(0, len(parts), 2):
            part_content = parts[i]
            if i > 0:
                current_part = parts[i-1] + parts[i]
                part_content = parts[i]
            
            # Within each part, split by article numbers at start of line
            # Pattern: newline followed by digit(s) and a period
            articles = re.split(r"\n\s*(\d+[A-Z]?)\.\s+", part_content)
            
            if len(articles) > 1:
                for j in range(1, len(articles), 2):
                    art_no = articles[j]
                    art_text = articles[j+1] if j+1 < len(articles) else ""
                    
                    chunks.append({
                        "chunk_id": f"art_{art_no}",
                        "text": f"{current_part.splitlines()[0] if 'PART' in current_part else current_part[:50]}\nArticle {art_no}\n{art_text.strip()}",
                        "metadata": {
                            "type": "article",
                            "article_no": art_no,
                            "part": current_part.splitlines()[0] if "PART" in current_part else "N/A",
                            "index": idx,
                            "citation_type": "article"
                        }
                    })
                    idx += 1
            else:
                # If no articles found in this section, add as a general chunk
                if part_content.strip():
                    chunks.append({
                        "chunk_id": f"part_section_{i}",
                        "text": part_content.strip(),
                        "metadata": {
                            "type": "section", 
                            "part": current_part.splitlines()[0] if "PART" in current_part else "N/A",
                            "index": idx,
                            "citation_type": "article"
                        }
                    })
                    idx += 1
            
        return chunks

    def save_chunks(self, chunks: List[Dict], output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=4)
        print(f"Saved {len(chunks)} chunks to {output_path}")

if __name__ == "__main__":
    raw_path = os.path.join(settings.PROCESSED_DATA_PATH, "raw_text.txt")
    output_path = os.path.join(settings.PROCESSED_DATA_PATH, "chunks.json")
    
    if os.path.exists(raw_path):
        chunker = ArticleChunker(raw_path)
        chunks = chunker.chunk_by_article()
        chunker.save_chunks(chunks, output_path)
    else:
        print(f"Please run pdf_parser.py first to generate {raw_path}")
