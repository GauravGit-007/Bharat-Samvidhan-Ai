import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama' or 'huggingface'
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Ollama Config
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3.1:8b")
    
    # Embedding Config
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    
    # Vector DB Config
    CHROMA_DB_PATH: str = os.path.join("data", "vector_db")
    COLLECTION_NAME: str = "constitution_articles"
    IPC_COLLECTION_NAME: str = "ipc_sections"
    
    # RAG Config
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 512))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 50))
    TOP_K: int = int(os.getenv("TOP_K", 5))
    USE_RERANKER: bool = os.getenv("USE_RERANKER", "True").lower() == "true"
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    # Paths
    RAW_DATA_PATH: str = os.path.join("data", "raw", "constitution_of_india.pdf")
    IPC_RAW_DATA_PATH: str = os.path.join("data", "raw", "ipc_json", "ipc.json")
    PROCESSED_DATA_PATH: str = os.path.join("data", "processed")

settings = Settings()
