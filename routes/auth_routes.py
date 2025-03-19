# routes/auth_routes.py
import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models import db
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Redirect logged in users
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not username or not password:
            error = 'Please provide both username and password.'
        else:
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                # Login successful
                login_user(user, remember=remember)
                logger.info(f"User {username} logged in successfully")
                
                # Get next page from query param or default to index
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                error = 'Invalid username or password.'
                logger.warning(f"Failed login attempt for username: {username}")
    
    return render_template('login.html', error=error)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration."""
    # Redirect logged in users
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password:
            error = 'Please fill in all required fields.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        else:
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                error = 'Username already exists.'
            elif User.query.filter_by(email=email).first():
                error = 'Email already registered.'
            else:
                # Create new user
                hashed_password = generate_password_hash(password).decode('utf-8')
                
                user = User(
                    username=username,
                    email=email,
                    password=hashed_password
                )
                
                try:
                    db.session.add(user)
                    db.session.commit()
                    
                    # Log in the new user
                    login_user(user)
                    logger.info(f"New user registered: {username}")
                    
                    return redirect(url_for('index'))
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error registering user: {str(e)}")
                    error = 'An error occurred during registration. Please try again.'
    
    return render_template('signup.html', error=error)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with update functionality."""
    error = None
    success = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update profile information
            email = request.form.get('email')
            
            if email != current_user.email:
                # Check if email already exists
                if User.query.filter_by(email=email).first():
                    error = 'Email already registered to another account.'
                else:
                    current_user.email = email
                    db.session.commit()
                    success = 'Profile updated successfully.'
        
        elif action == 'change_password':
            # Change password
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not check_password_hash(current_user.password, current_password):
                error = 'Current password is incorrect.'
            elif new_password != confirm_password:
                error = 'New passwords do not match.'
            elif len(new_password) < 8:
                error = 'New password must be at least 8 characters long.'
            else:
                current_user.password = generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                success = 'Password changed successfully.'
    
    return render_template('profile.html', error=error, success=success)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Request password reset."""
    # This would be implemented with email functionality
    # For now, just show a placeholder page
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    return render_template('reset_password_request.html')