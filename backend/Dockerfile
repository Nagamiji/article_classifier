FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
       --extra-index-url https://download.pytorch.org/whl/cpu \
       -r requirements.txt

# Copy application code
COPY . .

# Create directories with proper permissions
RUN mkdir -p /app/ml/artifacts /app/logs && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app/logs && \
    chmod -R 777 /app/ml/artifacts  # HF cache and models must be writable

# Set environment variable for Hugging Face cache
ENV TRANSFORMERS_CACHE=/app/ml/artifacts

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with Gunicorn + Uvicorn worker
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--log-level", "info"]
