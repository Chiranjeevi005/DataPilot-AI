import os
import json
import time
import requests
import logging
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:3000/api/upload" # Adjust port if needed, usually 3000 for Next.js appapi routes? 
# Wait, the prompt says "python src/api/upload/route.py (running)". 
# Phase 1 setup implies the upload endpoint might be running on a separate port or Next.js API route.
# The user state says `python src/api/upload/route.py` is running.
# Let's check `src/api/upload/route.py` to see what port it binds to. usually 5000 or 8000 for flask/python.

# I'll check port in a moment. For now assume port 5000 for python backend.

def generate_pdf(file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    elements = []
    
    data = [
        ['InvoiceID', 'Date', 'Customer', 'Amount', 'Status'],
        ['INV-001', '2023-01-01', 'Alice Corp', '100.50', 'Paid'],
        ['INV-002', '2023-01-02', 'Bob Inc', '200.00', 'Pending'],
        ['INV-003', '2023-01-03', 'Charlie LLC', '50.75', 'Paid'],
        ['INV-004', '2023-01-04', 'Dave Ltd', '1200.00', 'Overdue'],
        ['INV-005', '2023-01-05', 'Eve Ent', '300.25', 'Paid'],
    ]
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t)
    doc.build(elements)
    logger.info(f"Generated PDF at {file_path}")

def generate_json(file_path):
    data = {
        "metadata": {"generated_at": "2023-10-10", "source": "system"},
        "customers": [
            {"id": 1, "name": "Alice", "contacts": [{"type": "email", "val": "a@a.com"}]},
            {"id": 2, "name": "Bob", "contacts": []},
            {"id": 3, "name": "Charlie", "orders": 5},
            {"id": 4, "name": "Dave", "active": True}
        ]
    }
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Generated JSON at {file_path}")

def upload_and_check(file_path):
    # Determine URL
    # Assuming python backend is at 5000 based on standard flask apps, 
    # but I'll verify via context shortly. If 3000 is Next.js, and it proxies...
    # The user is running `python src/api/upload/route.py`.
    # Let's check that file later. Assuming http://localhost:5000/api/upload
    
    url = "http://localhost:5328/api/upload"
    
    files = {'file': open(file_path, 'rb')}
    logger.info(f"Uploading {file_path} to {url}...")
    try:
        r = requests.post(url, files=files)
        r.raise_for_status()
        res = r.json()
        job_id = res.get('jobId')
        logger.info(f"Job ID: {job_id}")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return False
        
    # Poll
    status_url = f"http://localhost:5328/api/job-status/{job_id}"
    # Actually, Phase 1 deliverables usually include status endpoint. 
    # If not, I can check Redis directly, but let's try HTTP first.
    
    for i in range(20):
        time.sleep(2)
        try:
            r = requests.get(status_url)
            # If status endpoint not implemented, we might fail here.
            # But let's assume it exists or we check redis.
            # Wait, `jobId` is returned.
            job_data = r.json()
            status = job_data.get('status')
            logger.info(f"Status: {status}")
            
            if status == 'completed':
                result_url = job_data.get('resultUrl')
                logger.info(f"Job completed. Result URL: {result_url}")
                
                # Fetch result
                # result_url is likely a file:// or blob url.
                # If file://, we can just read it if local.
                # If http://, download.
                
                if result_url.startswith('file:///'):
                     # requests won't fetch file://
                     path = result_url.replace('file:///', '')
                     # Windows fix
                     if ':' in path and path[2] == ':': # c:/...
                         pass # might need to strip leading /? file:///c:/... -> c:/...
                     elif os.name == 'nt' and path.startswith('c:/') or path.startswith('C:/'):
                         pass
                     else:
                        # try normal path
                        pass
                        
                     # dirty path fix
                     if os.name == 'nt':
                         # url2pathname
                         from urllib.request import url2pathname
                         path = url2pathname(result_url.replace('file:', ''))
                     
                     if os.path.exists(path):
                         with open(path, 'r') as f:
                             result_json = json.load(f)
                             return result_json
                     else:
                         logger.error(f"Result file not found at {path}")
                         return False
                return False
                
            if status == 'failed':
                logger.error(f"Job failed: {job_data.get('error')}")
                return False
                
        except Exception as e:
            # If status endpoint fails, maybe check output dir directly?
            # Or redis.
            # For this test script, failure to poll is failure.
            logger.warning(f"Polling error: {e}")
            
    logger.error("Timed out waiting for job")
    return False

def main():
    os.makedirs('dev-samples', exist_ok=True)
    
    pdf_path = os.path.abspath('dev-samples/invoices.pdf')
    json_path = os.path.abspath('dev-samples/customers.json')
    
    generate_pdf(pdf_path)
    generate_json(json_path)
    
    # Test PDF
    logger.info("--- Testing PDF ---")
    res_pdf = upload_and_check(pdf_path)
    if res_pdf:
        # Check structure
        if 'schema' in res_pdf and len(res_pdf['schema']) > 0:
             logger.info("SUCCESS: PDF tables extracted and schema generated.")
        elif 'text_extract' in res_pdf:
             logger.info("NOTE: PDF text fallback used.")
        else:
             logger.error("FAILURE: Unexpected output for PDF")
             print(res_pdf)
    else:
        logger.error("PDF Test Failed")

    # Test JSON
    logger.info("--- Testing JSON ---")
    res_json = upload_and_check(json_path)
    if res_json:
        if 'schema' in res_json and len(res_json['schema']) > 0:
             logger.info("SUCCESS: JSON normalized and schema generated.")
        else:
             logger.error("FAILURE: JSON schema missing")
             print(res_json)
    else:
        logger.error("JSON Test Failed")

if __name__ == "__main__":
    main()
