"""
Vercel serverless function entry point for Flask application.
This file routes all requests to the Flask app.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Export the Flask app for Vercel serverless functions
export = app
