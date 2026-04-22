"""
Vercel serverless function entry point for Flask application.
This file routes all requests to the Flask app with proper error handling.
"""

import sys
import os
import traceback
from json import dumps

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Flask app
try:
    from app import app as flask_app
    print("✅ Flask app imported successfully", file=sys.stderr)
except Exception as e:
    print(f"❌ Failed to import Flask app: {str(e)}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    
    # Create a fallback app that returns error info
    from flask import Flask, jsonify
    flask_app = Flask(__name__)
    
    @flask_app.route('/')
    @flask_app.route('/<path:path>')
    def error_handler(path=''):
        return jsonify({
            "error": "Failed to initialize Flask application",
            "details": str(e),
            "required_env_vars": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "SECRET_KEY", "DATABASE_URL (optional)"]
        }), 500

# Export the Flask app as the WSGI callable for Vercel
# The Vercel Python runtime will call this function with (request) as parameter
app = flask_app
