# models/user.py
from flask_login import UserMixin
from datetime import datetime
from models import db
from flask_bcrypt import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    """Model for user accounts."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # For future use - roles and permissions
    role = db.Column(db.String(20), default='user')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @classmethod
    def create_user(cls, username, email, password):
        """Create a new user with hashed password."""
        hashed_password = generate_password_hash(password).decode('utf-8')
        new_user = cls(
            username=username,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user
    
    def verify_password(self, password):
        """Check if provided password matches stored hash."""
        return check_password_hash(self.password, password)
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'