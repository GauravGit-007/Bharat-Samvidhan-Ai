import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from src.config.settings import settings

class Vectorizer:
    def __init__(self):
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embeddings = FastEmbedEmbeddings(
            model_name=settings.EMBEDDING_MODEL, # FastEmbed supports this natively
            cache_dir='./data/models'
        )
        print("Embedding model loaded successfully.")
        self.db_path = settings.CHROMA_DB_PATH

    def create_vector_db(self, chunks_path: str):
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found at {chunks_path}")
            
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["text"],
                metadata=chunk["metadata"]
            )
            documents.append(doc)
            
        print(f"Adding {len(documents)} documents to ChromaDB at {self.db_path}...")
        
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.db_path,
            collection_name=settings.COLLECTION_NAME
        )
        print("ChromaDB collection created.")
        vector_db.persist()
        print("Vector database created and persisted successfully.")

if __name__ == "__main__":
    try:
        chunks_path = os.path.join(settings.PROCESSED_DATA_PATH, "chunks.json")
        vectorizer = Vectorizer()
        vectorizer.create_vector_db(chunks_path)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
