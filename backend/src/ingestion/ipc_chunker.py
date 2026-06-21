import json
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from src.config.settings import settings

class IPCChunker:
    def __init__(self, raw_json_path: str, act_name: str, doc_type: str):
        self.raw_json_path = raw_json_path
        self.act_name = act_name
        self.doc_type = doc_type
        if not os.path.exists(raw_json_path):
            raise FileNotFoundError(f"JSON file not found at {raw_json_path}")

    def chunk_by_section(self) -> list[Document]:
        with open(self.raw_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs = []
        combined_key = "chapter,section,section_title,section_desc"
        for idx, item in enumerate(data):
            if combined_key in item:
                val = item[combined_key]
                if not val.strip():
                    continue
                import csv
                import io
                reader = csv.reader(io.StringIO(val))
                try:
                    parts = next(reader)
                except Exception:
                    continue
                if len(parts) >= 3:
                    sec_no = parts[1].strip()
                    if not sec_no or not (sec_no[0].isdigit() if sec_no else False):
                        continue
                    chapter = parts[0].strip()
                    sec_title = parts[2].strip()
                    sec_desc = parts[3].strip() if len(parts) >= 4 else ""
                else:
                    continue
            else:
                sec_no = str(item.get("Section", item.get("section", ""))).strip()
                sec_title = item.get("section_title", item.get("title", "")).strip()
                sec_desc = item.get("section_desc", item.get("description", "")).strip()
                chapter = str(item.get("chapter", "")).strip()
            
            if not sec_no or not sec_desc:
                continue
                
            content = f"[{self.act_name}] Section {sec_no}: {sec_title}\n{sec_desc}"
            docs.append(Document(
                page_content=content,
                metadata={
                    "type": self.doc_type,
                    "article_no": sec_no, # keep this key as article_no so frontend works without breaking
                    "section_title": sec_title,
                    "chapter": chapter,
                    "index": idx,
                    "citation_type": "section",
                    "act_name": self.act_name
                }
            ))
            
        return docs

if __name__ == "__main__":
    embeddings = FastEmbedEmbeddings(model_name=settings.EMBEDDING_MODEL, cache_dir='./data/models')
    vector_db = Chroma(
        persist_directory=settings.CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name=settings.IPC_COLLECTION_NAME
    )
    
    # Reset collection if exists, then add docs
    try:
        vector_db.delete_collection()
        vector_db = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=settings.IPC_COLLECTION_NAME
        )
        print("Deleted and re-created ChromaDB collection.")
    except Exception as e:
        print(f"Error resetting collection: {e}")
        
    acts = [
        {"name": "Indian Penal Code", "file": "ipc.json", "type": "ipc_section"},
        {"name": "Code of Criminal Procedure", "file": "crpc.json", "type": "crpc_section"},
        {"name": "Code of Civil Procedure", "file": "cpc.json", "type": "cpc_section"},
        {"name": "Indian Evidence Act", "file": "iea.json", "type": "iea_section"},
        {"name": "Negotiable Instruments Act", "file": "nia.json", "type": "nia_section"},
        {"name": "Hindu Marriage Act", "file": "hma.json", "type": "hma_section"},
        {"name": "Industrial Disputes Act", "file": "ida.json", "type": "ida_section"},
        {"name": "Motor Vehicles Act", "file": "MVA.json", "type": "mva_section"}
    ]
    
    for act in acts:
        json_path = os.path.join("data", "raw", "ipc_json", act["file"])
        print(f"\nProcessing {act['name']} from {json_path}...")
        try:
            chunker = IPCChunker(json_path, act_name=act["name"], doc_type=act["type"])
            docs = chunker.chunk_by_section()
            print(f"Extracted {len(docs)} sections.")
            
            # Add documents in batches to avoid overwhelming ChromaDB
            batch_size = 100
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i + batch_size]
                vector_db.add_documents(batch)
                print(f"  Ingested batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1}")
                
            print(f"Successfully ingested {act['name']} into ChromaDB.")
        except Exception as e:
            print(f"Error ingesting {act['name']}: {e}")
            
    print("\nAll statutory sections ingested successfully.")

