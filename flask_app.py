#!/usr/bin/env python3
"""
Flask application entry point for PythonAnywhere
This file should be named 'flask_app.py' in your PythonAnywhere account
"""
import os
import sys

# Add your project directory to the Python path
path = '/home/yourusername/file-sharing'  # Change 'yourusername' to your actual username
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables for production
os.environ['FLASK_CONFIG'] = 'production'
os.environ['FLASK_ENV'] = 'production'

# Import your application
from app_factory import create_app

# Create the application instance
application = create_app('production')

# This is what PythonAnywhere will use
app = application

if __name__ == "__main__":
    app.run(debug=False)