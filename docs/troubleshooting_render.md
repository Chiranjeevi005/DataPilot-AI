# Troubleshooting Render Deployments

## Common Issues

### 1. App not binding to $PORT
**Symptom**: Deploy fails with "Timed out waiting for port 10000".
**Fix**: Ensure `Start Command` uses `$PORT`.
- Backend: `gunicorn -b 0.0.0.0:$PORT ...`
- Frontend: `npm run start` (Next.js automatically respects `PORT`).

### 2. File Uploads Vanish
**Symptom**: You upload a file, it processes, but later "File not found".
**Cause**: Render file system is ephemeral. Files are deleted on restart/deploy.
**Fix**:
- Set `BLOB_ENABLED=true` env var.
- Configure S3/Object Store secrets.
- Check logs for "Blob storage disabled" warning.

### 3. Worker stuck or repeating jobs
**Symptom**: Job status stays "processing" forever.
**Cause**: Worker crashed or didn't handle SIGTERM.
**Fix**:
- Check usage of `rq` or custom worker loop.
- Ensure `JOB_TIMEOUT_SECONDS` is set to kill stuck jobs.
- Use `scripts/fetch_logs.sh worker-service` to see crash logs.

### 4. LLM API Errors (401/403)
**Symptom**: Analysis fails with "Authentication Error".
**Fix**:
- Check `OPENROUTER_API_KEY` in Render Dashboard -> Environment Groups.
- Ensure no leading/trailing spaces in the key.

### 5. Redis Connection Refused
**Symptom**: Backend cannot connect to Redis.
**Fix**:
- Ensure `REDIS_URL` is correct.
- If using Render Managed Redis, ensure services are in the same region and `ipAllowList` is set correctly (empty for internal access).

### 6. Build Fails (pip or npm)
**Symptom**: `npm install` or `pip install` fails.
**Fix**:
- Check `deployment/docker-compose.yml` for local drift vs `Dockerfile`.
- Ensure dependencies are in `requirements.txt` or `package.json`.
- Check Memory usage during build. Increase instance size if OOM.
