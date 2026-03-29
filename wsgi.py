"""
WSGI entry point for RAASU v2.0.0
For deployment using Gunicorn
"""

import os
from app import create_app

# Get environment (default to production for Render)
env = os.environ.get('FLASK_ENV', 'production')

# Create Flask app
app = create_app(env)