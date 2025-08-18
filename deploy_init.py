#!/usr/bin/env python3
"""
Deployment Initialization Script for EY File Sharing
Forces all paths to be within the project directory during deployment
"""
import os
import sys
from pathlib import Path

class DeploymentPathManager:
    def __init__(self):
        # Force absolute project directory detection
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            self.project_root = os.path.dirname(sys.executable)
        else:
            # Running as Python script
            self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        print(f"[DEPLOY] Project root detected: {self.project_root}")
        
        # CRITICAL: Force working directory change
        current_wd = os.getcwd()
        if current_wd != self.project_root:
            print(f"[DEPLOY] Changing working directory from {current_wd} to {self.project_root}")
            os.chdir(self.project_root)
            print(f"[DEPLOY] Working directory is now: {os.getcwd()}")
        else:
            print(f"[DEPLOY] Working directory already correct: {current_wd}")
    
    def get_absolute_paths(self):
        """Get all absolute paths for the application"""
        paths = {
            'base_dir': self.project_root,
            'uploads': os.path.join(self.project_root, 'uploads'),
            'logos': os.path.join(self.project_root, 'logos'),
            'static': os.path.join(self.project_root, 'static'),
            'templates': os.path.join(self.project_root, 'templates'),
            'database': os.path.join(self.project_root, 'file_sharing.db'),
            'static_css': os.path.join(self.project_root, 'static', 'css'),
            'static_js': os.path.join(self.project_root, 'static', 'js')
        }
        return paths
    
    def ensure_directory_structure(self):
        """Create all necessary directories with absolute paths"""
        paths = self.get_absolute_paths()
        
        directories_to_create = [
            paths['uploads'],
            paths['logos'],
            paths['static_css'],
            paths['static_js'],
            paths['templates']
        ]
        
        print("[DEPLOY] Creating directory structure...")
        for directory in directories_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"[DEPLOY] [OK] Directory ensured: {directory}")
                
                # Verify directory exists
                if os.path.exists(directory):
                    print(f"[DEPLOY] [OK] Verified directory exists: {directory}")
                else:
                    print(f"[DEPLOY] [ERROR] Directory not found after creation: {directory}")
                    
            except Exception as e:
                print(f"[DEPLOY] [ERROR] creating directory {directory}: {e}")
                raise
        
        print("[DEPLOY] Directory structure creation completed")
        return paths
    
    def setup_environment_variables(self):
        """Set environment variables to force correct paths"""
        paths = self.get_absolute_paths()
        
        # Set environment variables that the app will use
        os.environ['EY_PROJECT_ROOT'] = self.project_root
        os.environ['EY_UPLOAD_FOLDER'] = paths['uploads']
        os.environ['EY_LOGO_FOLDER'] = paths['logos']
        os.environ['EY_DATABASE_PATH'] = paths['database']
        
        print(f"[DEPLOY] Environment variables set:")
        print(f"[DEPLOY]   EY_PROJECT_ROOT={os.environ.get('EY_PROJECT_ROOT')}")
        print(f"[DEPLOY]   EY_UPLOAD_FOLDER={os.environ.get('EY_UPLOAD_FOLDER')}")
        print(f"[DEPLOY]   EY_LOGO_FOLDER={os.environ.get('EY_LOGO_FOLDER')}")
        print(f"[DEPLOY]   EY_DATABASE_PATH={os.environ.get('EY_DATABASE_PATH')}")
    
    def validate_deployment(self):
        """Validate that all paths are correct"""
        paths = self.get_absolute_paths()
        
        print("[DEPLOY] Validating deployment paths...")
        
        # Check current working directory
        current_wd = os.getcwd()
        if current_wd != self.project_root:
            print(f"[DEPLOY] [ERROR] CRITICAL ERROR: Working directory incorrect!")
            print(f"[DEPLOY]   Expected: {self.project_root}")
            print(f"[DEPLOY]   Actual: {current_wd}")
            return False
        else:
            print(f"[DEPLOY] [OK] Working directory correct: {current_wd}")
        
        # Check all directories exist
        validation_failed = False
        for name, path in paths.items():
            if name == 'database':
                # Database file might not exist yet, check parent directory
                parent_dir = os.path.dirname(path)
                if os.path.exists(parent_dir):
                    print(f"[DEPLOY] [OK] Database parent directory exists: {parent_dir}")
                else:
                    print(f"[DEPLOY] [ERROR] Database parent directory missing: {parent_dir}")
                    validation_failed = True
            elif name in ['uploads', 'logos', 'static_css', 'static_js']:
                if os.path.exists(path):
                    print(f"[DEPLOY] [OK] Directory exists: {path}")
                else:
                    print(f"[DEPLOY] [ERROR] Directory missing: {path}")
                    validation_failed = True
        
        if validation_failed:
            print("[DEPLOY] [FAILED] DEPLOYMENT VALIDATION FAILED!")
            return False
        else:
            print("[DEPLOY] [SUCCESS] DEPLOYMENT VALIDATION PASSED!")
            return True

def initialize_deployment():
    """Initialize deployment with forced path configuration"""
    print("="*60)
    print("EY FILE SHARING - DEPLOYMENT INITIALIZATION")
    print("="*60)
    
    try:
        # Create deployment manager
        deploy_manager = DeploymentPathManager()
        
        # Set up environment variables
        deploy_manager.setup_environment_variables()
        
        # Create directory structure
        paths = deploy_manager.ensure_directory_structure()
        
        # Validate deployment
        if not deploy_manager.validate_deployment():
            print("[DEPLOY] CRITICAL ERROR: Deployment validation failed!")
            sys.exit(1)
        
        print("[DEPLOY] [SUCCESS] Deployment initialization completed successfully!")
        print("="*60)
        
        return paths
        
    except Exception as e:
        print(f"[DEPLOY] CRITICAL ERROR during deployment initialization: {e}")
        print("="*60)
        sys.exit(1)

# Global variable to store deployment paths
DEPLOYMENT_PATHS = None

def get_deployment_paths():
    """Get deployment paths (initialize if not done yet)"""
    global DEPLOYMENT_PATHS
    if DEPLOYMENT_PATHS is None:
        DEPLOYMENT_PATHS = initialize_deployment()
    return DEPLOYMENT_PATHS

if __name__ == "__main__":
    # Run deployment initialization
    initialize_deployment()