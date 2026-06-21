# Bharat Samvidhan RAG - Project Scope

**Project Name**: Bharat Samvidhan AI  
**Tagline**: Constitutional Knowledge at Your Fingertips  
**Type**: RAG (Retrieval Augmented Generation) Pipeline for Indian Constitution

---

## 1. Project Overview

A production-grade RAG system that answers legal queries about the Constitution of India using semantic search and local LLM inference. Designed for real-world deployment with free-tier services.

**Use Cases**:
- Citizens understanding their fundamental rights
- Students studying constitutional law
- Quick reference for legal clauses and articles
- Rights-based query resolution (e.g., "Can police search without warrant?")

---

## 2. Asset Sources

### 2.1 Constitution Text (Primary Data)

**Option A: India Code (Recommended)**
- **URL**: https://www.indiacode.nic.in/constitution-of-india/
- **Format**: PDF (Official, amended up to 2023)
- **Download**: Search "Constitution of India" → Click PDF download
- **Save to**: `data/raw/constitution_of_india.pdf`
- **Why**: Official government source, includes all amendments

**Option B: Constitute Project (Backup)**
- **URL**: https://www.constituteproject.org/constitution/India_2020.pdf
- **Format**: PDF
- **Why**: Well-formatted, academic source

**Option C: Legislative Department**
- **URL**: https://legislative.gov.in/constitution-of-india
- **Format**: HTML (easier parsing)
- **Why**: Structured text, part-wise navigation

### 2.2 Amendment History
- **URL**: https://legislative.gov.in/amendment-acts/
- **Format**: List of all 106+ amendments
- **Use**: Metadata enrichment for chunks

### 2.3 Part-wise Summaries (Optional Enhancement)
- **Source**: Wikipedia - Constitution of India articles
- **URL**: https://en.wikipedia.org/wiki/Constitution_of_India
- **Use**: Add context to each part (I-XXII) for better retrieval

---

## 3. Tech Stack (Free-Tier Optimized)

### 3.1 Backend Stack

**LLM Inference**
- **Local**: Ollama with `llama3.1:8b` or `qwen2.5-coder:7b`
- **Hardware**: RTX 3050 6GB (sufficient for 7B-8B models)
- **Quantization**: Use Q4 or Q5 quantized models for speed
- **Serving**: Ollama API (localhost:11434)

**Embedding Model**
- **Model**: `BAAI/bge-large-en-v1.5` (1024 dimensions)
- **Alternative**: `all-MiniLM-L6-v2` (384 dim, faster)
- **Library**: `sentence-transformers`
- **Storage**: HuggingFace Hub (auto-cached locally)

**Vector Database**
- **Primary**: ChromaDB (persistent, lightweight)
- **Alternative**: FAISS (faster, in-memory)
- **Storage**: Local filesystem → Deploy with app

**Framework**
- **Backend**: FastAPI (async, fast, OpenAPI docs)
- **Orchestration**: LangChain (RAG pipeline, prompt templates)
- **Parsing**: PyMuPDF (PDF → text extraction)

### 3.2 Frontend Stack

**Framework**: React + TypeScript + Vite
**UI Library**: Tailwind CSS + shadcn/ui
**State**: React Query for API calls
**Deployment**: Vercel (free tier)

### 3.3 Deployment Architecture

```
Frontend (Vercel)
    ↓ HTTPS
Backend API (Render - Free Web Service)
    ↓
Ollama (Local during dev) → HuggingFace Inference API (production)
    ↓
ChromaDB (embedded in backend)
```

**Cost**: $0/month (all free tiers)

---

## 4. Project Structure

```
bharat-samvidhan-rag/
├── data/
│   ├── raw/                          # Downloaded PDFs
│   │   └── constitution_of_india.pdf
│   ├── processed/                    # Chunked data
│   │   ├── chunks.json              # Article chunks with metadata
│   │   └── metadata.json            # Part/schedule mappings
│   └── vector_db/                   # ChromaDB persistence
│       └── chroma.sqlite3
│
├── src/
│   ├── ingestion/
│   │   ├── pdf_parser.py           # PDF → raw text
│   │   ├── chunker.py              # Text → semantic chunks
│   │   └── vectorizer.py           # Chunks → embeddings
│   │
│   ├── retrieval/
│   │   ├── retriever.py            # Semantic + keyword search
│   │   ├── reranker.py             # Score & filter chunks
│   │   └── generator.py            # LLM response generation
│   │
│   ├── api/
│   │   ├── main.py                 # FastAPI app
│   │   ├── routes.py               # /query, /health endpoints
│   │   └── schemas.py              # Pydantic models
│   │
│   └── config/
│       ├── settings.py             # Environment config
│       └── prompts.py              # System prompts
│
├── frontend/                        # React app (separate repo)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   └── package.json
│
├── tests/
│   ├── eval_questions.json         # Test dataset
│   └── test_rag.py                 # Evaluation script
│
├── notebooks/
│   └── rag_experimentation.ipynb   # Jupyter for testing
│
├── requirements.txt
├── .env.example
├── Dockerfile                       # For Render deployment
└── README.md
```

---

## 5. Tech Stack Dependencies

### 5.1 Python Backend (`requirements.txt`)

```txt
# Core Framework
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
python-dotenv==1.0.1

# RAG Components
langchain==0.1.9
langchain-community==0.0.24
chromadb==0.4.24
sentence-transformers==2.5.1

# PDF Processing
PyMuPDF==1.23.26
pypdf==4.0.2

# Vector Search (Alternative)
faiss-cpu==1.7.4

# API & Utils
requests==2.31.0
pydantic-settings==2.2.1

# Optional: BM25 for hybrid search
rank-bm25==0.2.2
```

### 5.2 Ollama Models (Pre-download)

```bash
# Primary LLM (Best quality)
ollama pull llama3.1:8b

# Alternative (Faster inference)
ollama pull qwen2.5-coder:7b

# Lightweight option (if GPU memory constrained)
ollama pull gemma2:2b
```

### 5.3 Embedding Model (Auto-downloads from HuggingFace)

```python
# Primary: BAAI/bge-large-en-v1.5 (335M params, 1024 dim)
# Fallback: sentence-transformers/all-MiniLM-L6-v2 (22M params, 384 dim)
```

---

## 6. Deployment Strategy

### 6.1 Development (Local)

```bash
# Backend
cd bharat-samvidhan-rag
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### 6.2 Production (Free Tier)

**Backend on Render**:
- Service Type: Web Service (Free)
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port 10000`
- Environment Variables:
  - `OLLAMA_API_URL=https://api-inference.huggingface.co/models/...`
  - `HF_API_TOKEN=your_huggingface_token`
- Cold start: ~30s (acceptable for free tier)

**Vector DB**: 
- Embed ChromaDB files in Docker image
- Persistent disk (Render free tier: 512MB)

**LLM Inference**:
- Development: Local Ollama
- Production: HuggingFace Inference API (free tier: 30k tokens/month)
- Model: `meta-llama/Llama-3.1-8B-Instruct` or `Qwen/Qwen2.5-Coder-7B-Instruct`

**Frontend on Vercel**:
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: `VITE_API_URL=https://your-render-app.onrender.com`

---

## 7. Data Pipeline Workflow

### Phase 1: Ingestion (One-time setup)
1. Download Constitution PDF
2. Extract text with PyMuPDF
3. Chunk by articles (with metadata)
4. Generate embeddings using BGE-large
5. Store in ChromaDB with metadata:
   ```json
   {
     "chunk_id": "article_14",
     "text": "Full article text...",
     "metadata": {
       "article_no": 14,
       "part": "III",
       "part_name": "Fundamental Rights",
       "title": "Equality before law",
       "amendment_year": null
     }
   }
   ```

### Phase 2: Retrieval (Per query)
1. User query → Embedding
2. Semantic search (top-k=10)
3. Rerank by relevance score
4. Select top-3 chunks
5. Construct prompt with context
6. LLM generates answer with citations

### Phase 3: Response Format
```json
{
  "answer": "According to Article 14...",
  "citations": [
    {
      "article": "Article 14",
      "part": "III",
      "text": "The State shall not deny..."
    }
  ],
  "confidence": 0.92
}
```

---

## 8. Chunking Strategy

**Principle**: One article = One chunk (with context)

```python
{
  "chunk_id": "article_21",
  "text": """
    PART III - FUNDAMENTAL RIGHTS
    Article 21: Protection of life and personal liberty
    
    No person shall be deprived of his life or personal liberty 
    except according to procedure established by law.
  """,
  "metadata": {
    "article_no": 21,
    "part": "III",
    "keywords": ["life", "liberty", "procedure", "fundamental rights"]
  }
}
```

**Chunks per document**:
- ~400 articles → ~400 chunks
- 12 Schedules → ~50 chunks
- Total: ~450-500 chunks

---

## 9. Evaluation Metrics

### Test Dataset (`tests/eval_questions.json`)

```json
[
  {
    "question": "What is my right to equality?",
    "expected_articles": ["14", "15", "16"],
    "category": "fundamental_rights"
  },
  {
    "question": "Can police arrest me without a warrant?",
    "expected_articles": ["22"],
    "category": "arrest_rights"
  },
  {
    "question": "What is the right to education?",
    "expected_articles": ["21A"],
    "category": "fundamental_rights"
  }
]
```

**Metrics**:
- **Retrieval Accuracy**: Did it fetch the correct articles?
- **Citation Accuracy**: Are article references correct?
- **Answer Quality**: Manual review (1-5 scale)
- **Latency**: <3s end-to-end

---

## 10. System Prompts

### System Prompt Template

```python
SYSTEM_PROMPT = """You are Bharat Samvidhan AI, an expert on the Constitution of India.

Your role:
- Answer questions about Indian constitutional law
- Always cite specific Article numbers
- If information is not in the Constitution, say "This is not covered in the Constitution"
- Be precise, formal, and legally accurate

Context from Constitution:
{retrieved_chunks}

User Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. Cite articles explicitly (e.g., "According to Article 21...")
3. If uncertain, express it clearly
4. Keep answers concise but complete
"""
```

---

## 11. GPU Optimization (RTX 3050)

**Model Selection**:
- **Fits comfortably**: 7B-8B models (Q4 quantized)
- **Max context**: 4096 tokens (adjust based on VRAM)
- **Batch size**: 1 (streaming responses)

**Ollama Configuration** (`~/.ollama/config.json`):
```json
{
  "num_gpu": 1,
  "num_thread": 8,
  "num_ctx": 4096
}
```

**Expected Performance**:
- Inference speed: ~20-30 tokens/sec
- Response time: 2-5 seconds for 100-word answer

---

## 12. Free Tier Limits

| Service | Limit | Strategy |
|---------|-------|----------|
| Render (Backend) | 750 hrs/month, sleeps after 15min | Wake on request (30s cold start) |
| Vercel (Frontend) | 100GB bandwidth | Optimized React build |
| HuggingFace Inference | 30k tokens/month | Use for production only, local for dev |
| ChromaDB Storage | 512MB (Render disk) | ~500 chunks = <10MB |

---

## 13. Implementation Phases

### Phase 1: Data Preparation (Week 1)
- [ ] Download Constitution PDF
- [ ] Parse PDF → Extract text
- [ ] Create chunking pipeline
- [ ] Generate test questions (20 samples)

### Phase 2: RAG Pipeline (Week 1-2)
- [ ] Set up ChromaDB
- [ ] Implement embedding pipeline
- [ ] Build retrieval logic
- [ ] Integrate Ollama LLM
- [ ] Test with eval dataset

### Phase 3: API Development (Week 2)
- [ ] FastAPI routes (/query, /health)
- [ ] Pydantic schemas
- [ ] Error handling
- [ ] CORS setup for Vercel

### Phase 4: Frontend (Week 2-3)
- [ ] React UI with query input
- [ ] Display answers with citations
- [ ] Article reference panel
- [ ] Responsive design

### Phase 5: Deployment (Week 3)
- [ ] Dockerize backend
- [ ] Deploy to Render
- [ ] Deploy frontend to Vercel
- [ ] Configure HuggingFace Inference API
- [ ] End-to-end testing

---

## 14. Alternative Names (Choose One)

1. **Bharat Samvidhan AI** (Current choice)
2. **संविधान Sahayak** (Constitution Helper)
3. **Nyaya Mitra** (Law Friend)
4. **ConstitutionGPT India**
5. **Samvidhan Saarthi** (Constitution Guide)

**Recommended**: **Bharat Samvidhan AI**  
**URL**: `bharatsamvidhan.vercel.app`

---

## 15. Success Criteria

### MVP (Minimum Viable Product)
- [ ] Answers 80% of test questions correctly
- [ ] Cites correct article numbers
- [ ] <5 second response time
- [ ] Deployed and accessible online

### Production Ready
- [ ] 90%+ retrieval accuracy
- [ ] Handles edge cases (ambiguous queries)
- [ ] Mobile-responsive UI
- [ ] Analytics/logging for queries

---

## 16. Getting Started Checklist

### Pre-Coding Setup
- [ ] Create project directory: `bharat-samvidhan-rag/`
- [ ] Download Constitution PDF from India Code
- [ ] Install Ollama: `ollama pull llama3.1:8b`
- [ ] Create `requirements.txt` with dependencies
- [ ] Set up folder structure (data/, src/, tests/)
- [ ] Create 10 test questions in JSON
- [ ] Create `.env` file with:
  ```env
  OLLAMA_BASE_URL=http://localhost:11434
  EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
  CHUNK_SIZE=512
  CHUNK_OVERLAP=50
  TOP_K=10
  ```

### Ready to Code
Once assets are downloaded and folders are set up, you're ready to start with:
1. PDF parsing script
2. Chunking pipeline
3. Vectorization + ChromaDB setup
4. RAG retrieval logic
5. FastAPI endpoints

---

## 17. Resources & References

### Documentation
- **LangChain**: https://python.langchain.com/docs/
- **ChromaDB**: https://docs.trychroma.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Ollama API**: https://github.com/ollama/ollama/blob/main/docs/api.md

### Tutorials
- **RAG with LangChain**: https://python.langchain.com/docs/use_cases/question_answering/
- **BGE Embeddings**: https://huggingface.co/BAAI/bge-large-en-v1.5

### Datasets for Inspiration
- Indian Kanoon API (case law): https://api.indiankanoon.org/
- Constitution amendments: https://legislative.gov.in/

---

## 18. Contact & Support

**Developer**: Gaurav  
**Location**: Delhi, India  
**Hardware**: RTX 3050 6GB, WSL2 Ubuntu  
**Timeline**: 3 weeks to MVP  

---

**Last Updated**: May 15, 2026  
**Version**: 1.0  
**License**: MIT (Open Source)
