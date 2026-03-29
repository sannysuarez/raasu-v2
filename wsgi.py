"""
WSGI entry point for RAASU v2.0.0
For deployment using Gunicorn
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # add project root to Python path

from app import create_app

env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)