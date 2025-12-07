"""
Vercel Serverless Function for /api/upload endpoint
Simply exports the Flask app - Vercel's Python runtime handles the rest
"""

import os
import sys

# Ensure the project root and src directory are in the Python path
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')

for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import and export the Flask app
# Vercel's Python runtime will automatically handle WSGI
from src.api.upload.route import app

# That's it! Vercel will call the Flask app directly
