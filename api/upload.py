"""
Vercel Serverless Function for /api/upload endpoint
"""

import os
import sys

# Ensure the project root and src directory are in the Python path
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')

for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import the Flask app with all routes configured
from src.api.upload.route import app

# Vercel will call this handler
def handler(event, context):
    """
    Vercel serverless function handler for upload endpoint.
    """
    from werkzeug.wrappers import Request
    from io import BytesIO
    import json
    
    # Create WSGI environ from Vercel event
    body = event.get('body', '')
    if isinstance(body, str):
        body = body.encode('utf-8')
    
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', event.get('method', 'POST')),
        'SCRIPT_NAME': '',
        'PATH_INFO': '/api/upload',
        'QUERY_STRING': '',
        'CONTENT_TYPE': event.get('headers', {}).get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)),
        'SERVER_NAME': event.get('headers', {}).get('host', 'localhost'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(body),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in event.get('headers', {}).items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Call the Flask app
    response_data = []
    def start_response(status, headers):
        response_data.append((status, headers))
    
    try:
        app_response = app(environ, start_response)
        
        # Build the response
        status_code = int(response_data[0][0].split()[0])
        headers_dict = {k: v for k, v in response_data[0][1]}
        body = b''.join(app_response).decode('utf-8')
        
        return {
            'statusCode': status_code,
            'headers': headers_dict,
            'body': body
        }
    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        }
