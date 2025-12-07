# Deployment Configuration

This directory contains all deployment-related configuration files for DataPilot AI.

## Files

### Docker Configuration
- **`Dockerfile.backend`** - Docker image configuration for Python backend (FastAPI + Worker)
- **`Dockerfile.frontend`** - Docker image configuration for Next.js frontend
- **`docker-compose.yml`** - Local development Docker Compose setup

### Cloud Deployment
- **`antigravity.yml`** - Antigravity (Google Cloud) deployment configuration
- **`github-workflow.yml`** - GitHub Actions CI/CD workflow (place in `.github/workflows/` if using)

## Quick Start

### Local Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Antigravity Deployment
```bash
# Deploy to Antigravity
cd ..
./scripts/deploy_antigravity.sh

# Verify deployment
./scripts/verify_deploy.sh
```

## Environment Variables

Make sure to configure the following before deployment:
- Copy `.env.example` to `.env`
- Set `OPENROUTER_API_KEY` for LLM functionality
- Configure `REDIS_URL` for job queue
- Set `BLOB_ENABLED=true` and `BLOB_KEY` for cloud storage

See the main [README.md](../README.md) for complete setup instructions.
