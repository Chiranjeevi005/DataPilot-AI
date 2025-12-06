import os
import datetime
import random
import string
import logging

# Configure logging
# Note: Basic config here might be overridden by the main app, but good for standalone usage.
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'pdf'}
DEFAULT_MAX_SIZE = 20 * 1024 * 1024  # 20 MB

def generate_job_id() -> str:
    """Generates a job ID in the format job_YYYYMMDD_HHMMSS_<random4>."""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"job_{timestamp}_{random_suffix}"

def validate_file_extension(filename: str) -> bool:
    """Checks if the file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_file_size(size_bytes: int) -> bool:
    """Checks if the file size is within limits."""
    max_size = int(os.getenv('MAX_UPLOAD_SIZE_BYTES', DEFAULT_MAX_SIZE))
    return size_bytes <= max_size

def current_timestamp_iso() -> str:
    """Returns the current UTC timestamp in ISO format."""
    return datetime.datetime.utcnow().isoformat() + "Z"

def get_max_upload_size() -> int:
    return int(os.getenv('MAX_UPLOAD_SIZE_BYTES', DEFAULT_MAX_SIZE))
