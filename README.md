---
title: Bharat Samvidhan AI
emoji: ⚖️
colorFrom: indigo
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# ⚖️ Bharat Samvidhan AI


> **High-Precision Hybrid RAG Engine & Diagnostics Sandbox for Indian Constitutional and Statutory Law.**

**Bharat Samvidhan AI** is a state-of-the-art, offline-first Retrieval-Augmented Generation (RAG) system engineered to index, parse, and reason over the full corpus of the **Constitution of India** and primary Indian statutory codes: the **Indian Penal Code (IPC)**, **Code of Criminal Procedure (CrPC)**, **Code of Civil Procedure (CPC)**, and the **Indian Evidence Act (IEA)**. 

Featuring a decoupled, nostalgic typewriter-style **Diagnostics Compiler** (`/playground`), the platform allows legal professionals, AI engineers, and citizens to execute query pipelines and view deep-dive traces of vector search space hits, sparse keyword matches, and LLM synthesis live.

---

## 🔍 What It Does

1. **Hybrid Retrieval (Dense + Sparse)**:
   * **Dense Search**: Semantic vector matching using ChromaDB and a locally cached `BAAI/bge-small-en-v1.5` embeddings model.
   * **Sparse Search**: Keywords and exact statutory phrase extraction using a built-in `BM25Okapi` index initialized on startup.
2. **Domain-Specific Query Routing**:
   * Analyzes intent to segment queries between Constitutional (Fundamental Rights, Articles) and Statutory (crimes, penalties, civil procedures) schemas.
3. **Context Adjacency Recovery**:
   * Pulls neighboring sections from the SQLite index dynamically to preserve critical definitions, exemptions, and punishments surrounding legal matches.
4. **Dynamic User Memory Expiry & Consolidation**:
   * A background LLM-driven consolidation pipeline evaluates declaration inputs to update active user context, resolving profile contradictions and automatically pruning outdated memory keys.
5. **Seriousness Retro Diagnostic UI**:
   * Decoupled `/playground` sandbox featuring togglable **Obsidian Mode** (Stark B&W Retro) and **Parchment Mode** (Typewriter/Newspaper Editorial), complete with live latency analysis, prompt HUDs, and parallel citation comparators.

---

## 👥 Who Is It For?

*   **Legal Professionals (Advocates, Judges, and Clerks)**:
    *   To quickly retrieve cross-referenced legal citations, verify penalties, and study constitutional boundaries for complex casework offline.
*   **Law Students & Academic Researchers**:
    *   To study comparative constitutional law, map statutory dependencies, and explore how acts like the IPC interact with constitutional rights (e.g., Article 21 vs. Section 302).
*   **AI Researchers & Software Engineers**:
    *   Interested in production-grade hybrid search, SQLite Write-Ahead Logging (WAL) concurrency optimizations, and visual diagnostic tools for explainable AI.
*   **Indian Citizens**:
    *   To query rights, rules, and penal codes in plain conversational English, receiving clear, referenced legal summaries.

---

## ⚡ Quick Start & Deployment Modes

Bharat Samvidhan AI supports two deployment configurations: **Local Offline Mode** (using Ollama) and **Cloud API Mode** (using Groq). A dynamic selector in the UI allows switching between them seamlessly.

### 🔌 Model Availability & Fallback Flow
When using the **Groq Cloud Engine**, the backend executes a sequential fallback to maximize uptime:
1. **Primary LLM:** `llama-3.3-70b-versatile` (deep legal reasoning).
2. **Secondary Fallback:** `llama-3.1-8b-instant` (lower quota usage, fallback during 70B rate-limits).
3. **Outage Fallback:** A professional, user-friendly service interruption notice is returned if both models fail or are rate-limited, ensuring robust application behavior.

---

### 💻 Configuration 1: Local Offline Mode (Recommended for Developers)

Run the RAG system completely locally and privately without internet dependencies.

1. **Install Ollama:** Download and install Ollama from [ollama.com](https://ollama.com).
2. **Download LLM Model:** Pull the default local model in your terminal:
   ```bash
   ollama pull llama3.2:1b
   # Or for higher accuracy:
   ollama pull llama3.1:8b
   ```
3. **Configure Settings:** Make sure your `.env` contains the correct model name:
   ```env
   MODEL_NAME=llama3.2:1b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

---

### ☁️ Configuration 2: Cloud API Mode (For Production Deployments)

For high-speed, high-accuracy inference without local hardware requirements.

1. **Obtain Groq API Key:** Sign up at [Groq Console](https://console.groq.com) and create an API key.
2. **Configure environment:** Add your key to `.env`:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   ```
3. **Rate Limiting Protection:** When deployed, requests targeting the Groq Cloud endpoint are guarded by an in-memory token bucket rate limiter:
   - Burst limit: 3 requests per IP.
   - Refill rate: 1 token every 15 seconds (4 requests per minute limit).
   - Daily limit: 50 requests per IP per day.

---

### 🚀 Running the Web Server

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Bootstrap the application:** Launch the backend and frontend compiler using the boot scripts:
   * **Windows (PowerShell)**:
     ```powershell
     ./start.ps1
     ```
   * **Linux / macOS (Bash)**:
     ```bash
     ./start.sh
     ```
3. **Verify Models:** Run the validation script to check connectivity to Ollama and Groq API:
   ```bash
   python validate_models.py
   ```

Once started, access the main search app at `http://127.0.0.1:8000/` and the diagnostics sandbox at `http://127.0.0.1:8000/playground`.

