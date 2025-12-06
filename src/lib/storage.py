import os
import logging
import shutil
from pathlib import Path
import io
import urllib.parse
import urllib.request
from datetime import datetime

try:
    from .retry import retry_with_backoff
except ImportError:
    from retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Configuration from env
BLOB_RETRY_ATTEMPTS = int(os.getenv('BLOB_RETRY_ATTEMPTS', '3'))
RETRY_INITIAL_DELAY = float(os.getenv('RETRY_INITIAL_DELAY', '0.5'))
RETRY_FACTOR = float(os.getenv('RETRY_FACTOR', '2.0'))
RETRY_MAX_DELAY = float(os.getenv('RETRY_MAX_DELAY', '10'))

def get_storage_path(job_id: str, filename: str) -> str:
    """
    Determines the local storage path. 
    Uses project-local 'tmp_uploads' by default for easier inspection on Windows,
    or /tmp/uploads if on Linux/Mac/explicitly requested.
    """
    # For Windows dev friendliness, we use a local folder in the project root if on Windows
    # unless env var override. 
    base_dir = os.getenv('LOCAL_STORAGE_ROOT')
    if not base_dir:
        if os.name == 'nt':
            base_dir = os.path.join(os.getcwd(), 'tmp_uploads')
        else:
            base_dir = '/tmp/uploads'
            
    return os.path.join(base_dir, job_id, filename)

def save_file_to_blob(file_stream, filename: str, job_id: str) -> str:
    """
    Saves file to blob storage. 
    Currently a stub implementation that strictly directs to save_file_to_tmp
    unless BLOB_ENABLED is strictly true and we had an SDK.
    """
    if os.getenv('BLOB_ENABLED', 'false').lower() == 'true':
        # TODO: Implement actual Antigravity Blob SDK upload here.
        # For now, we simulate blob upload by saving locally but returning a fake blob URL 
        # or erroring if strict.
        logger.warning(f"BLOB_ENABLED is true but SDK not implemented. Falling back to local for job {job_id}")
        return save_file_to_tmp(file_stream, filename, job_id)
    
    return save_file_to_tmp(file_stream, filename, job_id)

def save_file_to_tmp(file_stream, filename: str, job_id: str) -> str:
    """
    Saves file to local temporary storage for development.
    Returns the file URL (file:// path).
    Uses retry logic for resilience.
    """
    file_path = get_storage_path(job_id, filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    def _save_operation():
        """Inner function for retry wrapper"""
        # Write stream to file
        with open(file_path, 'wb') as f:
            # Check if file_stream is bytes or stream
            if isinstance(file_stream, bytes):
                f.write(file_stream)
            else:
                # Reset stream position if possible
                if hasattr(file_stream, 'seek'):
                    try:
                        file_stream.seek(0)
                    except:
                        pass
                shutil.copyfileobj(file_stream, f)
        
        logger.info(f"Saved file locally for job {job_id} at {file_path}")
        
        # Return file:// URL
        abs_path = os.path.abspath(file_path)
        return Path(abs_path).as_uri()
    
    try:
        return retry_with_backoff(
            _save_operation,
            attempts=BLOB_RETRY_ATTEMPTS,
            initial_delay=RETRY_INITIAL_DELAY,
            factor=RETRY_FACTOR,
            max_delay=RETRY_MAX_DELAY,
            retry_exceptions=(IOError, OSError, PermissionError),
            operation_name=f"Save file {filename} for job {job_id}"
        )
    except Exception as e:
        logger.error(f"Failed to save file for job {job_id} after retries: {e}")
        raise

def ensure_local_path(file_url: str) -> str:
    """
    Ensures the file at file_url is available locally. 
    If it's a file:// URL, returns the local path.
    If it's http(s)://, downloads to a temporary file and returns that path.
    """
    logger.info(f"Ensuring local path for {file_url}")
    parsed = urllib.parse.urlparse(file_url)
    
    if parsed.scheme == 'file':
        file_path = urllib.request.url2pathname(parsed.path)
        # Fix Windows path issues if necessary
        if os.name == 'nt' and file_path.startswith('\\') and not os.path.exists(file_path) and os.path.exists(file_path[1:]):
             file_path = file_path[1:]
        return file_path
        
    elif parsed.scheme in ('http', 'https'):
        # Download to a temp file with retry
        filename = os.path.basename(parsed.path) or "downloaded_file"
        
        # Use our temp storage
        target_dir = os.path.join(os.getenv('LOCAL_STORAGE_ROOT') or 'tmp_uploads', 'downloads')
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{int(datetime.now().timestamp())}_{filename}")
        
        def _download_operation():
            """Inner function for retry wrapper"""
            logger.info(f"Downloading {file_url} to {target_path}")
            urllib.request.urlretrieve(file_url, target_path)
            return target_path
        
        try:
            return retry_with_backoff(
                _download_operation,
                attempts=BLOB_RETRY_ATTEMPTS,
                initial_delay=RETRY_INITIAL_DELAY,
                factor=RETRY_FACTOR,
                max_delay=RETRY_MAX_DELAY,
                retry_exceptions=(ConnectionError, TimeoutError, IOError, urllib.error.URLError),
                operation_name=f"Download {file_url}"
            )
        except Exception as e:
            logger.error(f"Failed to download {file_url} after retries: {e}")
            raise
    else:
        raise ValueError(f"Unsupported scheme: {parsed.scheme}")

