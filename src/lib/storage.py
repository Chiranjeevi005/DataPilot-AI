import os
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

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
    """
    file_path = get_storage_path(job_id, filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write stream to file
    try:
        with open(file_path, 'wb') as f:
            # Check if file_stream is bytes or stream
            if isinstance(file_stream, bytes):
                f.write(file_stream)
            else:
                shutil.copyfileobj(file_stream, f)
        
        logger.info(f"Saved file locally for job {job_id} at {file_path}")
        
        # Return file:// URL
        # Windows paths need proper formatting for file URL
        abs_path = os.path.abspath(file_path)
        return Path(abs_path).as_uri()
        
    except Exception as e:
        logger.error(f"Failed to save file for job {job_id}: {e}")
        raise
