# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base
WORKDIR /app

# Builder stage: install dependencies in a venv
FROM base AS builder

# Copy requirements.txt first for better caching (if present)
COPY --link requirements.txt requirements.txt

# Create virtual environment and install dependencies
RUN python -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && --mount=type=cache,target=/root/.cache/pip \
       .venv/bin/pip install -r requirements.txt

# Copy application code
COPY --link . .

# Final stage: minimal image with venv and app code
FROM base AS final

# Create non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /app

# Copy venv and app code from builder
COPY --from=builder --link /app/.venv /app/.venv
COPY --from=builder --link /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Default command (adjust as needed)
CMD ["python", "answer.py"]
