This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```                                                                                    

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

---

## Backend (Python)

The backend implementation for DataPilot AI Phase 1 handles file uploads and job queuing.

### Prerequisites

1.  **Python 3.11+** installed.
2.  **Redis** installed and running (or use Docker).

### Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Copy `env.example` to `.env` and adjust if necessary.
    ```bash
    cp env.example .env
    ```
    *Note: `.env` is typically gitignored.*

3.  **Start Redis (Docker):**
    ```bash
    docker run --name redis-server -p 6379:6379 -d redis
    ```

### Running the Server

Start the standalone Python dev server for the upload endpoint:
```bash
# Make sure project root is in PYTHONPATH if needed, or run as module
# Windows Powershell:
$env:PYTHONPATH="."
python src/api/upload/route.py

# Linux/Mac:
export PYTHONPATH=.
python src/api/upload/route.py
```
The server runs on `http://localhost:5328` by default.

### Testing

Run the provided test script (requires bash/curl):
```bash
./scripts/test_upload.sh
```

Or manually:
```bash
# Upload CSV
# Note: On Windows PowerShell, use 'curl.exe' instead of 'curl'
curl -F "file=@./dev-samples/sales_demo.csv" http://localhost:5328/api/upload

```

### File Storage & Inspection

- **Local Development**: Files are saved to `tmp_uploads/` in the project root (Windows friendly) or `/tmp/uploads` (Linux/Mac) if `BLOB_ENABLED=false`.
- **Blob Storage**: Toggle `BLOB_ENABLED=true` in `.env` to enable (requires valid `BLOB_KEY` and SDK implementation).

### API Endpoints

- **POST /api/upload**
    - **Multipart**: `file=@path/to/file.csv`
    - **JSON**: `{"fileUrl": "...", "filename": "..."}`
    - **Returns**: `{"jobId": "job_...", "status": "submitted"}`

---

## Backend Worker (Phase 3)

The specific worker process handles `data_jobs` from Redis, processing them (simulation) and generating results.

### Running the Worker

The worker listens to Redis queue `data_jobs`.

```bash
# Using helper script
./scripts/run_worker.sh

# Or manually
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/worker.py
```

### Testing the Worker

1. Start Redis.
2. Start the Upload API (see above) if performing full flow.
3. Start the Worker (in a separate terminal).
4. Run the test flow:
   ```bash
   ./scripts/test_worker_flow.sh
   ```

### Worker Configuration

The worker uses the following `.env` settings:
- `SIMULATED_WORK_SECONDS`: Duration of simulated processing (default: 3).
- `WORKER_POLL_INTERVAL`: Redis polling interval in seconds (default: 1).
- `RESULTS_DIR`: Directory to store result JSONs if not using Blob (default: `/tmp/datapilot/results` or relative to project on Windows).

---

## Backend Phase 4: Data Processing & EDA

The Phase 4 worker implements real data processing for CSV, XLSX, and JSON files.

### Features
- **File Parsing**: Robust parsing with encoding fallback (UTF-8/Latin-1) and error handling.
- **Schema Inference**: Detects types (date, numeric, categorical, etc.), missing counts, and unique counts.
- **KPIs**: Row/Col counts, duplicates, and numeric stats (sum, mean, max, etc.).
- **Smart Charts**: Automatically generates specs for time-series (Line) and categorical distributions (Bar).
- **Quality Score**: Heuristic score (0-100) based on missingness, duplicates, and consistency.

### Result JSON Structure
The worker attempts to generate a `result.json` saved to storage:

```json
{
  "jobId": "job_...",
  "fileInfo": { "name": "data.csv", "rows": 100, "cols": 5, "type": "csv" },
  "schema": [
    { "name": "Date", "inferred_type": "datetime", "missing_count": 0, "unique_count": 9, "sample_values": ["2023-01-01"] }
  ],
  "kpis": {
    "rowCount": 100,
    "colCount": 5,
    "missingCount": 2,
    "numDuplicates": 0,
    "numericStats": { "Revenue": { "sum": 50000.0, "mean": 500.0, ... } }
  },
  "cleanedPreview": [
    { "Date": "2023-01-01", "Revenue": 500 }
  ],
  "chartSpecs": [
    { "id": "chart_timeseries_1", "type": "line", "xKey": "date", "yKey": "value", "data": [...] }
  ],
  "qualityScore": 85,
  "processedAt": "2025-12-06T..."
}
```

### Quality Score Logic
- **Base**: 100
- **Penalties**:
  - Missing Values: - (Percent Missing * 30), capped at 30 points.
  - Duplicates: -10 points if > 1% rows are duplicates.
- **Result**: `max(0, 100 - penalties)`

### Testing Phase 4
Run the automated test which uploads a messy CSV and validates the output:
```bash
./scripts/test_phase4.sh
```

---

## Backend Phase 6: LLM Insights (Gemini)

The Phase 6 worker integration adds automated AI business insights using Gemini.

### Setup
1. **API Key**: Set `GEMINI_API_KEY` in `.env`.
   - Get key from [Google AI Studio](https://aistudio.google.com/).
2. **Model**: Optional `GEMINI_MODEL` (default: `gemini-1.5-flash`).

### Features
- **Business Summary**: 3-5 high-level insights derived from EDA (KPIs, Schema, Preview).
- **Evidence**: Structured citations (aggregates or specific row examples) backing the insights.
- **Fail-Safe**:
  - **Retry Logic**: Automatically retries on JSON parsing errors.
  - **Fallback**: Returns a graceful "Analysis unavailable" message if API fails, ensuring the job still completes.
  - **Mock Mode**: Set `LLM_MOCK=true` to simulate LLM responses for local dev/testing without costs.

### Reprocessing
To re-run the LLM analysis on an *already processed* job (e.g. to iterate on prompts):
```bash
./scripts/reprocess_job.sh <jobId>
```
The script reads the existing `result.json`, re-sends context to LLM, and updates the insights in-place.

### Replacing Gemini
To use a different provider (e.g. OpenAI, Anthropic):
1. Modify `src/lib/llm_client.py`.
2. Update the `generate_insights` function to call the new provider.
3. Ensure the prompt logic remains consistent (Inputs: Schema/KPIs, Output: JSON).

---

## Backend Phase 7: Production Hardening

Phase 7 makes the DataPilot backend production-ready with retry/backoff policies, job timeouts, cancellation, and structured error handling.

### Features

#### 1. Retry & Backoff Logic
All transient operations use exponential backoff with jitter:
- **Blob Operations**: 3 attempts (configurable via `BLOB_RETRY_ATTEMPTS`)
- **LLM Calls**: 2 attempts (configurable via `LLM_RETRY_ATTEMPTS`)
- **HTTP Downloads**: 3 attempts

**Algorithm**:
```
delay = min(max_delay, initial_delay * factor^(attempt-1))
delay *= random.uniform(0.9, 1.1)  # ±10% jitter
```

**Configuration** (`.env`):
```bash
BLOB_RETRY_ATTEMPTS=3
LLM_RETRY_ATTEMPTS=2
RETRY_INITIAL_DELAY=0.5
RETRY_FACTOR=2.0
RETRY_MAX_DELAY=10
```

#### 2. LLM Circuit Breaker
Prevents cascading failures when LLM service is down:
- Tracks consecutive failures within a sliding time window
- Opens circuit after threshold failures
- Uses deterministic fallback during cooldown period
- Automatically closes after cooldown

**Configuration**:
```bash
LLM_CIRCUIT_THRESHOLD=5        # failures to open circuit
LLM_CIRCUIT_WINDOW=300         # seconds (5 min)
LLM_CIRCUIT_COOLDOWN=600       # seconds (10 min)
```

**Behavior**:
- Circuit OPEN → All LLM calls use fallback (no API calls)
- Circuit CLOSED → Normal operation with retries
- Fallback provides generic insights based on KPIs

#### 3. Job Timeout
Server-enforced timeout prevents runaway jobs:
- Set at job creation (`timeoutAt` field)
- Checked periodically during processing
- Enforced by `/api/job-status` endpoint

**Configuration**:
```bash
JOB_TIMEOUT_SECONDS=600  # 10 minutes default
```

**Behavior**:
- Job exceeds timeout → status set to `failed`
- Error code: `timeout`
- `error.json` created in blob storage

#### 4. Job Cancellation
Cancel jobs via API endpoint:

**Endpoint**: `POST /api/cancel?jobId=<id>`

**Request**:
```bash
curl -X POST "http://localhost:5328/api/cancel?jobId=job_abc123"
# or JSON body
curl -X POST http://localhost:5328/api/cancel \
  -H "Content-Type: application/json" \
  -d '{"jobId": "job_abc123"}'
```

**Response**:
```json
{
  "jobId": "job_abc123",
  "status": "cancelled",
  "cancelledAt": "2025-12-06T10:30:00Z"
}
```

**Behavior**:
- Worker checks cancellation before and during processing
- Cancelled jobs do NOT produce `result.json`
- Cannot cancel completed/failed jobs

#### 5. Error Handling & error.json
On failure, an `error.json` is saved to blob storage:

**Structure**:
```json
{
  "jobId": "job_abc123",
  "status": "failed",
  "error": "timeout",
  "message": "Job exceeded maximum processing time",
  "timestamp": "2025-12-06T10:30:00Z"
}
```

**Error Codes**:
- `timeout` - Job exceeded `JOB_TIMEOUT_SECONDS`
- `processing_error` - General processing failure
- `blob_upload_failed` - Storage operation failed after retries
- `worker_shutdown` - Worker terminated during processing

**Job Status Fields**:
```json
{
  "jobId": "job_abc123",
  "status": "failed",
  "error": "timeout",
  "errorMessage": "Job exceeded maximum processing time",
  "resultUrl": "file:///path/to/error.json",
  "createdAt": "2025-12-06T10:00:00Z",
  "updatedAt": "2025-12-06T10:10:00Z"
}
```

#### 6. Client Polling Strategy
Recommended exponential backoff for status polling:

**Algorithm**:
```javascript
const delays = [1000, 2000, 4000, 8000, 15000]; // ms
let attempt = 0;
const maxWait = 600000; // 10 minutes

while (elapsed < maxWait) {
  const status = await fetchJobStatus(jobId);
  
  if (status === 'completed' || status === 'failed' || status === 'cancelled') {
    break;
  }
  
  const delay = delays[Math.min(attempt, delays.length - 1)];
  await sleep(delay);
  attempt++;
}
```

**Configuration**:
```bash
CLIENT_MAX_WAIT_SECONDS=600  # 10 minutes
```

### Testing Phase 7

Four test scripts validate production hardening:

#### 1. Blob Retry Test
```bash
./scripts/test_phase7_retry_blob.sh
```
Tests retry logic for blob operations (requires manual failure injection for full test).

#### 2. LLM Failure Test
```bash
./scripts/test_phase7_llm_fail.sh
```
Tests LLM retry and fallback by using invalid API key.

**Expected**:
- 2 retry attempts
- Deterministic fallback used
- Job completes with `status: completed`
- `issues` field contains LLM failure indicator

#### 3. Cancellation Test
```bash
./scripts/test_phase7_cancel.sh
```
Tests job cancellation at various stages.

**Expected**:
- Cancelled jobs remain `status: cancelled`
- No `result.json` produced
- Cannot cancel completed jobs

#### 4. Timeout Test
```bash
./scripts/test_phase7_timeout.sh
```
Tests server-side timeout enforcement.

**Expected**:
- Jobs exceeding timeout marked as `failed`
- Error code: `timeout`
- `error.json` created

### Graceful Shutdown
Worker handles SIGINT/SIGTERM gracefully:
- Completes current processing step
- Marks in-progress job as `failed` with `error: worker_shutdown`
- Exits cleanly

**Test**:
```bash
# Start worker
python src/worker.py

# In another terminal, send SIGTERM
kill -TERM <worker_pid>
```

### Monitoring & Observability
All operations log structured messages:
```json
{
  "timestamp": "2025-12-06T10:30:00Z",
  "level": "INFO",
  "jobId": "job_abc123",
  "step": "llm_call",
  "message": "LLM call (deepseek/deepseek-r1): Attempt 1/2",
  "duration_ms": 1234
}
```

**Key Log Messages**:
- `"Attempt {n}/{max}"` - Retry attempts
- `"Circuit breaker OPENING"` - Circuit breaker triggered
- `"Job {id} was cancelled"` - Cancellation detected
- `"Job {id} has timed out"` - Timeout enforced

### Production Deployment Checklist

- [ ] Set `JOB_TIMEOUT_SECONDS` appropriate for workload
- [ ] Configure `OPENROUTER_API_KEY` for LLM
- [ ] Set circuit breaker thresholds based on expected load
- [ ] Enable blob storage (`BLOB_ENABLED=true`)
- [ ] Set up Redis persistence
- [ ] Configure worker auto-restart (systemd, supervisor, etc.)
- [ ] Set up log aggregation (CloudWatch, Datadog, etc.)
- [ ] Monitor circuit breaker state
- [ ] Set up alerts for high failure rates
- [ ] Test graceful shutdown in production environment

### Environment Variables Reference

See `.env.example` for complete list. Key Phase 7 variables:

```bash
# Timeouts
JOB_TIMEOUT_SECONDS=600
CLIENT_MAX_WAIT_SECONDS=600

# Retry Configuration
LLM_RETRY_ATTEMPTS=2
BLOB_RETRY_ATTEMPTS=3
RETRY_INITIAL_DELAY=0.5
RETRY_FACTOR=2.0
RETRY_MAX_DELAY=10

# Circuit Breaker
LLM_CIRCUIT_THRESHOLD=5
LLM_CIRCUIT_WINDOW=300
LLM_CIRCUIT_COOLDOWN=600

# LLM
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=deepseek/deepseek-r1
```
