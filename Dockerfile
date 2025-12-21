# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for Pocket Portals FastAPI application
# Python 3.12 with security hardening and optimized layer caching

# ============================================================================
# Stage 1: Builder - Install dependencies and build application
# ============================================================================
FROM python:3.12-slim AS builder

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency specifications first (cache optimization)
COPY pyproject.toml README.md ./

# Install dependencies
# Using --no-cache-dir to reduce image size
# Using pip directly since we're installing from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.12-slim AS runtime

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser pyproject.toml ./

# Expose port
EXPOSE 8888

# Health check
# Checks /health endpoint every 30s with 3s timeout
# Starts after 10s, allows 3 retries before marking unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')" || exit 1

# Switch to non-root user
USER appuser

# Environment variables
ENV PORT=8888 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Start application
# Uses $PORT environment variable for deployment flexibility (e.g., Render, Heroku)
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}
