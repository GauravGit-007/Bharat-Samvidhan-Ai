FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY src/ ./src

# Copy vector database and raw data
COPY data/ ./data

# Pre-download and cache FastEmbed model so it's baked into the image
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='./data/models')"

# Expose default port
EXPOSE 8000

# Define default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV LLM_PROVIDER=groq
ENV MODEL_NAME=llama-3.3-70b-versatile

# Fix permissions so the Hugging Face Spaces non-root user (UID 1000) can write to data directories, vector db, and history logs
RUN chmod -R 777 /app

# Command to run uvicorn server
CMD ["sh", "-c", "python -m uvicorn src.api.main:app --host $HOST --port $PORT"]
