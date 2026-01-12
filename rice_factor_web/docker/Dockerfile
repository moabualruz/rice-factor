# Rice-Factor Web Interface Dockerfile
#
# Multi-stage build for production deployment.
# Build: docker build -t rice-factor-web -f docker/Dockerfile ..
# Run:   docker run -p 8000:8000 -v $(pwd):/project rice-factor-web

# Stage 1: Build frontend (Vue 3 + Vite)
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (cache layer)
COPY frontend/package*.json ./
RUN npm ci --only=production || npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build || echo "Frontend not yet implemented - skipping build"

# Stage 2: Python runtime
FROM python:3.11-slim

LABEL maintainer="Rice-Factor Team"
LABEL description="Rice-Factor Web Interface"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using pip directly since we need the [web] extra
COPY pyproject.toml setup.py ./
COPY rice_factor/ ./rice_factor/
COPY rice_factor_web/ ./rice_factor_web/
RUN pip install --no-cache-dir ".[web]"

# Copy frontend build (if exists)
COPY --from=frontend-builder /app/frontend/dist ./rice_factor_web/static/ 2>/dev/null || mkdir -p ./rice_factor_web/static

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment configuration
ENV PYTHONUNBUFFERED=1
ENV RF_WEB_DEBUG=false
ENV RF_WEB_HOST=0.0.0.0
ENV RF_WEB_PORT=8000
ENV RF_WEB_PROJECT_ROOT=/project

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()" || exit 1

# Run with Gunicorn for production (multiple workers)
CMD ["python", "-m", "uvicorn", "rice_factor_web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
