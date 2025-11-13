# syntax=docker/dockerfile:1

# =============================
# PDBot Production Dockerfile - v0.6.0
# Multi-stage build for optimized image size and reproducibility
# =============================

FROM python:3.11-slim AS base

# Set up environment variables for pip and python
ENV PIP_CACHE_DIR=/root/.cache/pip \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# =============================
# Builder stage: install dependencies in a venv
# =============================
FROM base AS builder

# Install minimal system dependencies (curl for healthcheck, git for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first for better cache utilization
COPY --link requirements.txt /app/requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv /app/.venv \
    && . /app/.venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# =============================
# Final stage: copy app code and set up runtime
# =============================
FROM base AS final

# Create a non-root user for security
RUN useradd -m pdbotuser
USER pdbotuser

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code (excluding secrets, .env, git, IDE files)
COPY --link . /app

# Streamlit configuration: headless mode, disable telemetry
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose Streamlit port
EXPOSE 8501

# Healthcheck: verify Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint: start Streamlit app
CMD ["streamlit", "run", "src/app.py", "--server.port", "${STREAMLIT_SERVER_PORT}"]
