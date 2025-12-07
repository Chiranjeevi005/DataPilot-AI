import os
import sys
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load env
load_dotenv()

# Import Blueprints
try:
    from src.api.upload.route import upload_bp
    from src.api.health.route import health_bp
    from src.api.cancel.route import cancel_bp
except ImportError:
    # Try importing without src prefix if running from inside src or different context
    try:
        from api.upload.route import upload_bp
        from api.health.route import health_bp
        from api.cancel.route import cancel_bp
    except ImportError as e:
        print(f"Failed to import blueprints: {e}")
        # Creating dummy blueprints to allow app to start even if broken, 
        # allowing debugging via logs
        from flask import Blueprint
        upload_bp = Blueprint('upload', __name__)
        health_bp = Blueprint('health', __name__)
        cancel_bp = Blueprint('cancel', __name__)

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    # Allow all origins for now, or restrictive based on env
    CORS(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Register Blueprints
    app.register_blueprint(upload_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(cancel_bp)
    
    @app.route('/')
    def index():
        return jsonify({
            "service": "DataPilot AI Backend",
            "status": "running",
            "endpoints": [
                "/api/health",
                "/api/upload",
                "/api/job-status/<id>",
                "/api/results/<id>",
                "/api/cancel"
            ]
        })
        
    logger.info("DataPilot AI Backend initialized")
    return app

# Expose app for Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5328))
    print(f"Starting DataPilot AI Backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
