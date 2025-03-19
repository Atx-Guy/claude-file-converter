# init_db.py
import os
import logging
from flask import Flask
from models import db
from models.user import User
from models.conversion import Conversion
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create a Flask application for database initialization."""
    app = Flask(__name__)
    app.config.from_object(config.DevelopmentConfig)
    db.init_app(app)
    return app

def init_db():
    """Initialize the database by creating tables and adding initial data."""
    app = create_app()
    
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database tables created successfully!")
        
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            logger.info("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                password='$2b$12$mxZ9VK6V5C8bPX2OHTAWn.gRVEQnrc0JWZfynFJc2FqIm1o4KF8zW',  # hashed 'adminpassword'
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created successfully!")

def reset_db():
    """Reset the database by dropping all tables and recreating them."""
    app = create_app()
    
    with app.app_context():
        logger.warning("Dropping all database tables...")
        db.drop_all()
        logger.info("Database tables dropped successfully!")
        
        logger.info("Recreating database tables...")
        db.create_all()
        logger.info("Database tables recreated successfully!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_db()
    else:
        init_db()