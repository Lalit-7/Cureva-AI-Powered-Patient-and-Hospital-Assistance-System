"""
Vercel serverless function entry point for Flask application.
This file routes all requests to the Flask app.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects the app to be available as 'app' in the module
# This is the WSGI app that Vercel will call
