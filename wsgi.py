"""
WSGI entry point for Vercel deployment.
This file is used by Vercel to run the Flask application.
"""

from app import app

if __name__ == "__main__":
    app.run()
