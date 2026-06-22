from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Union
from src.retrieval.generator import Generator
from src.config.settings import settings
from src.api.rate_limiter import groq_rate_limiter
import uvicorn
import os

import json
from datetime import datetime
import uuid

app = FastAPI(title="Bharat Samvidhan AI API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize generator lazily to avoid overhead if not used immediately
generator = None

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    query: str
    chat_history: List[Message] = []
    model_provider: str = "local"  # "local" or "groq"
    focus: Union[str, List[str]] = "both"  # accepts a single string or a list of strings (e.g. ["marriage", "evidence"])
    session_id: str = "default"

class QueryResponse(BaseModel):
    query: str
    answer: str
    latency: float
    model_used: str = ""
    documents: List[Dict[str, Any]]

# Ensure directories exist
HISTORY_FILE = os.path.join("data", "processed", "rag_history.json")
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

def log_rag_response(query: str, answer: str, latency: float, documents: List[Dict[str, Any]], model_used: str = ""):
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except Exception:
                    history = []
        
        # Create a new record
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "latency": latency,
            "model_used": model_used,
            "documents": documents
        }
        
        # Prepend to make sure the newest is at the top
        history.insert(0, record)
        
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error logging RAG response: {e}")

generator_error = None

@app.on_event("startup")
async def startup_event():
    global generator, generator_error
    try:
        generator = Generator()
    except Exception as e:
        import traceback
        generator_error = f"{e}\n{traceback.format_exc()}"
        print(f"Error initializing generator: {e}")
        traceback.print_exc()

@app.get("/health")
def health_check():
    import chromadb
    return {
        "status": "healthy" if not generator_error else "error",
        "model": settings.MODEL_NAME,
        "chromadb_version": chromadb.__version__,
        "error": generator_error
    }

@app.get("/api/status")
def get_system_status():
    return {
        "model_name": settings.MODEL_NAME,
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "ollama_url": settings.OLLAMA_BASE_URL,
        "status": "online" if generator else "initializing"
    }

def check_ollama_available():
    import urllib.request
    import json
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.5) as response:
            if response.getcode() == 200:
                body = response.read().decode('utf-8')
                data = json.loads(body)
                models = [m.get('name') for m in data.get('models', [])]
                if models:
                    return True, f"Ollama is running with {len(models)} model(s)."
                return False, "Ollama is running but has no models installed."
    except Exception:
        pass
    return False, "Ollama is offline or unreachable."

def check_groq_available():
    if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 10:
        return True, "Groq Cloud API key is configured."
    return False, "Groq API key is missing or not configured in .env."

@app.get("/api/models/status")
def get_models_availability():
    local_ok, local_msg = check_ollama_available()
    groq_ok, groq_msg = check_groq_available()
    return {
        "local": {
            "available": local_ok,
            "message": local_msg,
            "model": settings.MODEL_NAME
        },
        "groq": {
            "available": groq_ok,
            "message": groq_msg,
            "model": "llama-3.3-70b-versatile -> llama-3.1-8b-instant"
        }
    }

@app.get("/api/history")
def get_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/history/clear")
def clear_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query", response_model=QueryResponse)
async def query_constitution(request_data: QueryRequest, request: Request, background_tasks: BackgroundTasks):
    if generator is None:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    
    # Rate Limiting check for Groq Cloud
    if request_data.model_provider == "groq":
        client_ip = request.client.host if request.client else "127.0.0.1"
        allowed, reason = groq_rate_limiter.check_limit(client_ip)
        if not allowed:
            raise HTTPException(status_code=429, detail=reason)
            
    try:
        chat_history_dicts = [{"role": msg.role, "content": msg.content} for msg in request_data.chat_history]
        response = generator.generate_rag_response(
            request_data.query, 
            chat_history=chat_history_dicts, 
            provider=request_data.model_provider,
            focus=request_data.focus,
            session_id=request_data.session_id
        )
        
        # Run fact extraction in the background (using local default)
        background_tasks.add_task(generator.extract_and_save_user_data, request_data.query, "local", request_data.session_id)
        
        # Log the response in history
        log_rag_response(
            query=response["query"],
            answer=response["answer"],
            latency=response["latency"],
            model_used=response.get("model_used", ""),
            documents=response["documents"]
        )
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query/stream")
async def query_constitution_stream(request_data: QueryRequest, request: Request, background_tasks: BackgroundTasks):
    if generator is None:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    
    # Rate Limiting check for Groq Cloud
    if request_data.model_provider == "groq":
        client_ip = request.client.host if request.client else "127.0.0.1"
        allowed, reason = groq_rate_limiter.check_limit(client_ip)
        if not allowed:
            raise HTTPException(status_code=429, detail=reason)
            
    # Run user fact extraction in the background (using local default)
    background_tasks.add_task(generator.extract_and_save_user_data, request_data.query, "local", request_data.session_id)
    
    from fastapi.responses import StreamingResponse
    
    async def sse_generator():
        try:
            chat_history_dicts = [{"role": msg.role, "content": msg.content} for msg in request_data.chat_history]
            full_response_text = ""
            retrieved_docs = []
            final_latency = 0.0
            model_used = settings.MODEL_NAME
            
            for chunk in generator.generate_rag_stream(
                request_data.query, 
                chat_history=chat_history_dicts, 
                provider=request_data.model_provider,
                focus=request_data.focus,
                session_id=request_data.session_id
            ):
                if chunk["type"] == "documents":
                    retrieved_docs = chunk["documents"]
                    yield f"event: documents\ndata: {json.dumps(chunk['documents'])}\n\n"
                elif chunk["type"] == "token":
                    full_response_text += chunk["content"]
                    yield f"event: token\ndata: {json.dumps(chunk['content'])}\n\n"
                elif chunk["type"] == "done":
                    final_latency = chunk["latency"]
                    model_used = chunk.get("model_used", model_used)
                    yield f"event: done\ndata: {json.dumps({'latency': chunk['latency'], 'model_used': model_used})}\n\n"
            
            # Log the final response in history
            log_rag_response(
                query=request_data.query,
                answer=full_response_text,
                latency=final_latency,
                model_used=model_used,
                documents=retrieved_docs
            )
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/api/query/debug")
async def query_constitution_debug(request_data: QueryRequest, request: Request):
    if generator is None:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    try:
        chat_history_dicts = [{"role": msg.role, "content": msg.content} for msg in request_data.chat_history]
        trace = generator.generate_debug_trace(
            request_data.query, 
            chat_history=chat_history_dicts, 
            provider=request_data.model_provider,
            focus=request_data.focus
        )
        return trace
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playground")
def get_playground():
    from fastapi.responses import HTMLResponse
    file_path = os.path.join(os.path.dirname(__file__), "playground.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>RAG Diagnostics Playground template not found.</h1>", status_code=404)

# Serve static files if build directory exists
from fastapi.staticfiles import StaticFiles
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist"))
if not os.path.exists(frontend_dist_path):
    # Fallback to legacy path for root-level execution structures
    frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
