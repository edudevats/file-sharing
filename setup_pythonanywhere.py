#!/usr/bin/env python3
"""
Setup script for PythonAnywhere deployment
Run this once after uploading your files to initialize the database and directories
"""
import os
import sys
from app_factory import create_app

def setup_pythonanywhere():
    """Initialize the application for PythonAnywhere"""
    print("Setting up EY File Sharing for PythonAnywhere...")
    
    # Create application instance
    app = create_app('production')
    
    with app.app_context():
        print("✓ Application created successfully")
        
        # Create necessary directories
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
        print("✓ Created upload and logo directories")
        
        # Database is automatically initialized in app_factory.py
        print("✓ Database initialized")
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update flask_app.py with your correct username path")
        print("2. Set up your web app in PythonAnywhere dashboard")
        print("3. Point to flask_app.py as your WSGI file")
        print("4. Change the SECRET_KEY in production")

if __name__ == "__main__":
    setup_pythonanywhere()