# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install PyTorch CPU-only first (avoid CUDA bloat)
RUN uv pip install --system \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN uv pip install --system \
    streamlit>=1.40.0 \
    pandas>=2.2.0 \
    psycopg2-binary>=2.9.9 \
    openai>=1.54.0 \
    python-dotenv>=1.0.0 \
    numpy>=2.0.0 \
    rank-bm25>=0.2.2 \
    scikit-learn>=1.5.0 \
    sentence-transformers>=2.2.0 \
    requests>=2.31.0

# Copy application code
COPY yoga_assistant/ ./yoga_assistant/
COPY data/ ./data/
COPY .env.template .env

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')"

# Entry point script to initialize database and start app
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
