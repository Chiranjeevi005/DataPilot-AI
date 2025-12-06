import os
import sys
import json
import time
import signal
import redis
import threading

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path so imports work whether run from root or src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobs import process_job
from observability import log_info, log_error, log_exception, increment, flush_metrics

COMPONENT = "worker"

shutdown_requested = False
current_job_id = None
heartbeat_thread = None

def update_heartbeat(redis_client):
    """
    Update worker heartbeat in Redis.
    Health check endpoint uses this to verify worker is alive.
    """
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + "Z"
        redis_client.set("worker:heartbeat", timestamp, ex=120)  # 2 minute expiry
        log_info(COMPONENT, "Heartbeat updated", step="heartbeat", timestamp=timestamp)
    except Exception as e:
        log_error(COMPONENT, f"Failed to update heartbeat: {e}", step="heartbeat")

def heartbeat_worker(redis_client):
    """
    Background thread that updates heartbeat periodically.
    """
    global shutdown_requested
    heartbeat_interval = int(os.getenv('WORKER_HEARTBEAT_INTERVAL', '30'))
    
    log_info(COMPONENT, f"Heartbeat worker started (interval: {heartbeat_interval}s)", step="heartbeat")
    
    while not shutdown_requested:
        try:
            update_heartbeat(redis_client)
            time.sleep(heartbeat_interval)
        except Exception as e:
            log_error(COMPONENT, f"Heartbeat worker error: {e}", step="heartbeat")
            time.sleep(5)
    
    log_info(COMPONENT, "Heartbeat worker stopped", step="heartbeat")

def signal_handler(signum, frame):
    global shutdown_requested
    log_info(COMPONENT, f"Received signal {signum}. Shutting down gracefully...", step="shutdown")
    shutdown_requested = True
    
    # Flush metrics before shutdown
    try:
        flush_metrics()
        log_info(COMPONENT, "Metrics flushed on shutdown", step="shutdown")
    except Exception as e:
        log_error(COMPONENT, f"Failed to flush metrics on shutdown: {e}", step="shutdown")
    
    # If currently processing a job, mark it as failed
    if current_job_id:
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            job_key = f"job:{current_job_id}"
            job_data_str = r.get(job_key)
            if job_data_str:
                job_data = json.loads(job_data_str)
                if job_data.get('status') == 'processing':
                    from datetime import datetime
                    job_data['status'] = 'failed'
                    job_data['error'] = 'worker_shutdown'
                    job_data['errorMessage'] = 'Worker shutdown during processing'
                    job_data['updatedAt'] = datetime.utcnow().isoformat() + "Z"
                    r.set(job_key, json.dumps(job_data))
                    log_info(COMPONENT, "Marked job as failed due to shutdown", 
                            job_id=current_job_id, step="shutdown")
                    increment("jobs_failed_total")
        except Exception as e:
            log_error(COMPONENT, f"Error marking job as failed during shutdown: {e}", 
                     job_id=current_job_id, step="shutdown")

def run_worker():
    global shutdown_requested, current_job_id, heartbeat_thread
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    poll_interval = int(os.getenv('WORKER_POLL_INTERVAL', '1'))
    
    log_info(COMPONENT, f"Worker starting. Connecting to Redis at {redis_url}...", step="startup")
    
    try:
        r = redis.from_url(redis_url)
        r.ping()
        log_info(COMPONENT, "Connected to Redis successfully", step="startup")
    except Exception as e:
        log_error(COMPONENT, f"Failed to connect to Redis: {e}", step="startup")
        return

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=heartbeat_worker, args=(r,), daemon=True)
    heartbeat_thread.start()
    
    # Initial heartbeat
    update_heartbeat(r)

    log_info(COMPONENT, "Listening for jobs on 'data_jobs' queue...", step="startup")
    
    while not shutdown_requested:
        try:
            # BRPOP blocks for 'timeout' seconds. 
            # Returns (queue_name, value) or None if timeout.
            item = r.brpop(['data_jobs'], timeout=poll_interval)
            
            if item:
                queue_name, payload_bytes = item
                try:
                    payload_str = payload_bytes.decode('utf-8')
                    job_payload = json.loads(payload_str)
                    
                    job_id = job_payload.get('jobId')
                    current_job_id = job_id
                    
                    log_info(COMPONENT, "Job dequeued from queue", 
                            job_id=job_id, step="dequeue",
                            fileName=job_payload.get('fileName'))
                    
                    increment("jobs_received_total")
                    
                    # Check for cancellation before starting
                    if job_id:
                        status_key = f"job:{job_id}"
                        current_status_payload = r.get(status_key)
                        if current_status_payload:
                            current_status = json.loads(current_status_payload).get('status')
                            if current_status == 'cancelled':
                                log_info(COMPONENT, "Job was cancelled before processing. Skipping.",
                                        job_id=job_id, step="dequeue")
                                current_job_id = None
                                continue

                    # Process the job
                    process_job.process_job(r, job_payload)
                    current_job_id = None
                    
                except json.JSONDecodeError as e:
                    log_error(COMPONENT, "Failed to decode job payload JSON", 
                             step="dequeue", error=str(e))
                    current_job_id = None
                except Exception as e:
                    log_exception(COMPONENT, "Unexpected error processing job", 
                                 exc_info=e, job_id=current_job_id, step="process")
                    current_job_id = None
            
            # If no item, loop continues (checking shutdown_requested)
            
        except redis.exceptions.ConnectionError as e:
            log_error(COMPONENT, "Redis connection lost. Retrying in 5 seconds...", 
                     step="redis_connection", error=str(e))
            time.sleep(5)
        except Exception as e:
            log_exception(COMPONENT, "Worker loop error", exc_info=e, step="main_loop")
            time.sleep(1)

    log_info(COMPONENT, "Worker shutdown complete", step="shutdown")

if __name__ == "__main__":
    run_worker()

