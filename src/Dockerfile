# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
WORKDIR /app

# Builder stage: install dependencies in a venv
FROM base AS builder

# Copy only requirements first for better cache usage
COPY --link requirements.txt ./

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
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Expose port (adjust as needed, e.g. 8000)
EXPOSE 8000

# Default command (adjust as needed)
CMD ["python", "app.py"]
