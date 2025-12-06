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
