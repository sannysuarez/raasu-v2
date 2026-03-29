"""
RAASU v2.0.0 - Web-based Thermal Printer POS System
Configuration template (example) for public repository
"""

import os

# Environment variable setup
ENV = os.environ.get('FLASK_ENV', 'development')  # 'development' or 'production'
DEBUG = ENV == 'development'

# Database
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///raasu.db')  # replace with your DB URL in production

# Flask secret
SECRET_KEY = os.environ.get('SECRET_KEY', 'replace-with-your-secret-key')

# Thermal printer settings
PRINTER_PORT = os.environ.get('PRINTER_PORT', '/dev/ttyUSB0')  # replace with actual printer port
PRINTER_BAUDRATE = int(os.environ.get('PRINTER_BAUDRATE', 9600))  # replace with printer baudrate if different

# Venture/Business information (editable by admin)
VENTURE_NAME = os.environ.get('VENTURE_NAME', 'Your POS System Name')
VENTURE_ADDRESS = os.environ.get('VENTURE_ADDRESS', 'Your Address Here')

"""
Example:

FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/raasu
SECRET_KEY=some-long-random-secret
PRINTER_PORT=/dev/ttyUSB0
PRINTER_BAUDRATE=9600
VENTURE_NAME=RAASU POS System
VENTURE_ADDRESS="123 Lagos Street, Nigeria""""