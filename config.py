# config.py
import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'replace_with_your_super_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload size
    
    # File format settings
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'aac', 'm4a'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'txt', 'md', 'html'}
    
    # MIME types
    ALLOWED_AUDIO_MIME_TYPES = {
        'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/flac', 
        'audio/aac', 'audio/x-m4a', 'audio/mp3'
    }
    ALLOWED_IMAGE_MIME_TYPES = {
        'image/png', 'image/jpeg', 'image/gif', 'image/webp',
        'image/bmp', 'image/tiff'
    }
    ALLOWED_DOCUMENT_MIME_TYPES = {
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain', 
        'text/markdown', 
        'text/html'
    }
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///development.db'
    

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///production.db')
    SECRET_KEY = os.environ.get('SECRET_KEY')  # This should be set in production
    
    # Use secure cookies in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True