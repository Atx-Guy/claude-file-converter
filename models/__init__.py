# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without binding to a specific app yet
db = SQLAlchemy()

# Import models after db is defined to avoid circular imports
from .user import User
from .conversion import Conversion

# Make models available at package level
__all__ = ['db', 'User', 'Conversion']