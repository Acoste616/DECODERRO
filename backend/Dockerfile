# ============================================
# ULTRA v3.0 Backend Dockerfile
# Target Platform: Railway
# Base Image: Python 3.11 Slim
# ============================================

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
# - gcc: C compiler for building native extensions
# - libpq-dev: PostgreSQL development headers for psycopg2
# - build-essential: Build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir: Don't cache packages (reduces image size)
# --user: Install to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only runtime dependencies
# - libpq5: PostgreSQL client library (runtime only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Add Python user packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/

# Copy data files for seeding
COPY seed.py .
COPY DATA_01_RAG.md .
COPY DATA_02_Golden_Standards.md .

# Create non-root user for security
# (Optional but recommended for production)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
# Railway will inject PORT env var, but default to 8000
EXPOSE 8000

# Health check endpoint
# Railway uses this to verify container health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Start command
# Railway can override this via Procfile or railway.toml
# Use PORT env var from Railway, default to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
