# Docker Configuration

Docker files for containerized deployment of PDBot.

## Files

- **Dockerfile** - Multi-stage production Docker image
- **docker-compose.yml** - Docker Compose configuration (recommended)
- **compose.yaml** - Alternative Compose format
- **.dockerignore** - Files to exclude from Docker build

## Usage

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t pdbot:2.0.0 -f docker/Dockerfile .

# Run container
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/feedback:/app/feedback \
  -e QDRANT_URL=http://host.docker.internal:6333 \
  --name pdbot \
  pdbot:2.0.0
```

## Requirements

- Docker 20.10+
- Docker Compose 2.0+ (optional, recommended)
- Ollama running on host (port 11434)
- Qdrant running on host (port 6333) or use Docker Compose
