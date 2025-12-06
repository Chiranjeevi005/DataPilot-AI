import os
import sys
import json
import time
import logging
import signal
import redis

# Add src to path so imports work whether run from root or src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobs import process_job

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("worker")

shutdown_requested = False
current_job_id = None

def signal_handler(signum, frame):
    global shutdown_requested
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    shutdown_requested = True
    
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
                    logger.info(f"Marked job {current_job_id} as failed due to shutdown")
        except Exception as e:
            logger.error(f"Error marking job as failed during shutdown: {e}")

def run_worker():
    global shutdown_requested, current_job_id
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    poll_interval = int(os.getenv('WORKER_POLL_INTERVAL', '1'))
    
    logger.info(f"Worker starting. Connecting to Redis at {redis_url}...")
    
    try:
        r = redis.from_url(redis_url)
        r.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return

    logger.info("Listening for jobs on 'data_jobs' queue...")
    
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
                    
                    # Check for cancellation before starting
                    if job_id:
                        status_key = f"job:{job_id}"
                        current_status_payload = r.get(status_key)
                        if current_status_payload:
                            current_status = json.loads(current_status_payload).get('status')
                            if current_status == 'cancelled':
                                logger.info(f"Job {job_id} was cancelled before processing. Skipping.")
                                current_job_id = None
                                continue

                    # Process the job
                    process_job.process_job(r, job_payload)
                    current_job_id = None
                    
                except json.JSONDecodeError:
                    logger.error("Failed to decode job payload JSON")
                    current_job_id = None
                except Exception as e:
                    logger.error(f"Unexpected error processing job: {e}", exc_info=True)
                    current_job_id = None
            
            # If no item, loop continues (checking shutdown_requested)
            
        except redis.exceptions.ConnectionError:
            logger.error("Redis connection lost. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            time.sleep(1)

    logger.info("Worker shutdown complete.")

if __name__ == "__main__":
    run_worker()

