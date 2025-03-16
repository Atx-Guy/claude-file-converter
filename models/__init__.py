# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without binding to a specific app yet
db = SQLAlchemy()