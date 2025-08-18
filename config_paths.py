#!/usr/bin/env python3
"""
Path Configuration for EY File Sharing Application
Ensures all paths are relative to the project directory
"""
import os

def get_base_dir():
    """Get the base directory of the project"""
    return os.path.dirname(os.path.abspath(__file__))

def get_project_paths():
    """Get all project paths relative to base directory"""
    base_dir = get_base_dir()
    
    paths = {
        'base_dir': base_dir,
        'uploads': os.path.join(base_dir, 'uploads'),
        'logos': os.path.join(base_dir, 'logos'), 
        'static': os.path.join(base_dir, 'static'),
        'templates': os.path.join(base_dir, 'templates'),
        'database': os.path.join(base_dir, 'file_sharing.db'),
        'static_css': os.path.join(base_dir, 'static', 'css'),
        'static_js': os.path.join(base_dir, 'static', 'js')
    }
    
    return paths

def ensure_directories():
    """Create all necessary directories"""
    paths = get_project_paths()
    
    directories = [
        paths['uploads'],
        paths['logos'],
        paths['static_css'], 
        paths['static_js'],
        paths['templates']
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Directory ensured: {directory}")

if __name__ == "__main__":
    print("EY File Sharing - Path Configuration")
    print("="*50)
    
    paths = get_project_paths()
    print(f"Base Directory: {paths['base_dir']}")
    print(f"Upload Folder: {paths['uploads']}")
    print(f"Logo Folder: {paths['logos']}")
    print(f"Database: {paths['database']}")
    
    print("\nEnsuring directories exist...")
    ensure_directories()
    print("\n[SUCCESS] Path configuration completed!")