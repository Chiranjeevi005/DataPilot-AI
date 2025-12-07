# Deploying DataPilot AI to Render

This guide outlines the steps to deploy the full DataPilot AI stack (Next.js Frontend, Python Backend, Worker, Redis) to Render.

## Architecture

- **Web Service (`web-service`)**: Next.js 14 Frontend.
- **Web Service (`api-service`)**: Python/Flask Backend API (Gunicorn).
- **Worker (`worker-service`)**: Background worker for long-running data processing.
- **Redis (`datapilot-redis`)**: Managed Redis for job queue.
- **Cron (`cleanup-job`)**: Scheduled maintenance script.

## Prerequisites

1. **Render Account**: [Sign up](https://render.com).
2. **Render CLI**: [Install instructions](https://render.com/docs/cli).
3. **Secrets**: You need keys for OpenAI/OpenRouter, S3/Object Store.

## Deployment Steps

### Method 1: Infrastructure as Code (Recommended)

1. **Push Code**: Ensure `render.yaml` and Dockerfiles are committed and pushed to your repo.
2. **Connect to Render**:
   - Go to Render Dashboard -> Blueprints.
   - Click "New Blueprint Instance".
   - Connect your GitHub repository.
   - Render will detect `render.yaml`.
3. **Configure Secrets**:
   - The Blueprint will ask for `datapilot-secrets` (API keys, S3 creds). Fill these in.
   - Click "Apply".

### Method 2: CLI Deployment

1. **Login**:
   ```bash
   render login
   ```
2. **Create Secrets**:
   Set secrets referenced in `render.yaml` before deploying (or Render will prompt/fail).
   ```bash
   ./scripts/render_set_secret.sh api-service OPENROUTER_API_KEY sk-...
   ```
3. **Deploy**:
   ```bash
   ./scripts/deploy_render.sh
   # Or manually
   render services create --file render.yaml
   ```

## Post-Deployment Validation

1. **Run Smoke Tests**:
   ```bash
   ./scripts/run_smoke_tests.sh https://api-your-app.onrender.com https://web-your-app.onrender.com
   ```
   This script performs an upload, polls for completion, and checks results.

2. **Check Logs**:
   ```bash
   ./scripts/fetch_logs.sh api-service
   ./scripts/fetch_logs.sh worker-service
   ```

## secrets Management

Never commit `.env`.
Use the Dashboard to manage Environment Groups (`shared-secrets`) or use the CLI.

Required Secrets:
- `OPENROUTER_API_KEY`: For LLM.
- `OBJECT_STORE_URL`, `S3_BUCKET`, `OBJECT_STORE_KEY`, `OBJECT_STORE_SECRET`: For file storage.
- `BLOB_ENABLED`: Set to `true`.

## Scaling

- **Services**: Start with `Starter` plan. Scale `worker-service` if processing queue builds up.
- **Redis**: Use Managed Redis. 25MB is usually enough for job queues.
- **LLM**: Monitor OpenRouter usage.
