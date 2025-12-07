import os
import sys

# Add project paths
project_root = os.getcwd()
src_path = os.path.join(project_root, 'src')
for path in [project_root, src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import the Flask app - Vercel will use it as WSGI app
from src.api.upload.route import app
