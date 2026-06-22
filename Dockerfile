# --- Build Stage for React Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package descriptors and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source code and build
COPY frontend/ ./
RUN npm run build

# --- Execution Stage ---
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend assets from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy backend application source
COPY backend/src/ ./src

# Copy vector database and raw data
COPY backend/data/ ./data

# Define cache paths for Hugging Face and Sentence Transformers
ENV HF_HOME=/app/data/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/data/models

# Pre-download and cache FastEmbed and CrossEncoder models so they are baked into the image
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='./data/models')" && \
    python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device='cpu')"

# Expose default Hugging Face Spaces port (7860)
EXPOSE 7860

# Define environment variables for production
ENV HOST=0.0.0.0
ENV PORT=7860
ENV LLM_PROVIDER=groq
ENV MODEL_NAME=llama-3.3-70b-versatile

# Fix permissions so the Hugging Face Spaces non-root user (UID 1000) can write to data directories, vector db, and history logs
RUN chmod -R 777 /app

# Command to run uvicorn server
CMD ["sh", "-c", "python -m uvicorn src.api.main:app --host $HOST --port $PORT"]
