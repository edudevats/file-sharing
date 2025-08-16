import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    LOGO_FOLDER = os.environ.get('LOGO_FOLDER', 'logos')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,pdf,doc,docx,txt,zip').split(','))
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///file_sharing.db')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    # Use a more secure secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ey-file-sharing-super-secret-key-change-this-in-production-2024')
    # For PythonAnywhere, use absolute paths
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    LOGO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logos')
    DATABASE_URL = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'file_sharing.db')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    UPLOAD_FOLDER = 'test_uploads'
    LOGO_FOLDER = 'test_logos'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}