# app.py
import os
import subprocess
import logging
import mimetypes
import traceback
import io
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User
from models.conversion import Conversion
from services.audio_service import AudioService
from services.image_service import ImageService
from services.document_service import DocumentService
from services.pdf_service import PDFService
from routes.pdf_routes import pdf_bp
from routes.auth_routes import auth_bp
from routes.conversion_routes import conversion_bp
from routes.api_routes import api_bp
from utils.file_utils import allowed_file, get_file_extension, create_temp_directory
from utils.feature_detector import FeatureDetector

import config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Configure database
db.init_app(app)

# Initialize services
audio_service = AudioService()
image_service = ImageService()
document_service = DocumentService()
pdf_service = PDFService()

# Detect available features
available_features = {
    'pdf': FeatureDetector.get_pdf_features(),
    'document': FeatureDetector.get_document_features(),
    'image': FeatureDetector.get_image_features(),
    'audio': FeatureDetector.get_audio_features()
}

# Log available features
logger.info("Available PDF features: %s", available_features['pdf'])
logger.info("Available document features: %s", available_features['document'])
logger.info("Available image features: %s", available_features['image'])
logger.info("Available audio features: %s", available_features['audio'])

# Create temp directories
create_temp_directory(app.config['TEMP_FOLDER'])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pdf_bp)
app.register_blueprint(conversion_bp)
app.register_blueprint(api_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_features():
    """Make available features accessible in templates."""
    return {
        'features': available_features
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/history')
@login_required
def history():
    # Get user's conversion history
    conversions = Conversion.query.filter_by(user_id=current_user.id)\
                                 .order_by(Conversion.created_at.desc())\
                                 .limit(50)\
                                 .all()
    return render_template('history.html', conversions=conversions)

@app.route('/batch')
def batch_processing():
    return render_template('batch.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/convert')
def convert():
    conversion_type = request.args.get('type', 'general')
    if conversion_type not in ['general', 'audio', 'image', 'document']:
        conversion_type = 'general'
    return render_template(f'convert/{conversion_type}.html')

@app.route('/convert-file', methods=['POST'])
def convert_file_route():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No selected file'}), 400
        
    # Get original filename without extension
    original_filename = os.path.splitext(file.filename)[0]
    
    filename = file.filename.lower()
    input_format = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    output_format = request.form.get('output_format', '').lower()
    
    # Get custom filename if provided, otherwise use original filename + "copy"
    custom_filename = request.form.get('custom_filename')
    if custom_filename and custom_filename.strip():
        output_filename = f"{custom_filename}.{output_format}"
    else:
        output_filename = f"{original_filename}_copy.{output_format}"
    
    # Save uploaded file to temp directory
    input_path = os.path.join(app.config['TEMP_FOLDER'], f"temp_input.{input_format}")
    output_path = os.path.join(app.config['TEMP_FOLDER'], f"temp_output.{output_format}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Determine file type and use appropriate service
        file_type = determine_file_type(input_format, output_format)
        
        if file_type == 'audio':
            # Convert audio file
            logger.info(f"Converting audio from {input_format} to {output_format}")
            audio_service.convert_audio(input_path, output_path)
            operation = 'convert_audio'
        elif file_type == 'image':
            # Convert image file
            logger.info(f"Converting image from {input_format} to {output_format}")
            image_service.convert_image(input_path, output_path)
            operation = 'convert_image'
        elif file_type == 'document':
            # Convert document
            logger.info(f"Converting document from {input_format} to {output_format}")
            document_service.convert_document(input_path, output_path)
            operation = 'convert_document'
        else:
            return jsonify({'error': 'Unsupported conversion'}), 400
        
        # Record conversion for logged in users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation=operation,
                input_filename=file.filename,
                output_filename=output_filename
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Read the converted file
        with open(output_path, 'rb') as f:
            file_data = f.read()
        
        # Clean up files
        try:
            os.remove(input_path)
            os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
        
        # Determine MIME type
        mime_type = mimetypes.guess_type(output_filename)[0]
        if not mime_type:
            if output_format in ['mp3', 'ogg', 'wav', 'flac', 'aac', 'm4a']:
                mime_type = f'audio/{output_format}'
            elif output_format in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                mime_type = f'image/{output_format}'
            elif output_format == 'pdf':
                mime_type = 'application/pdf'
            elif output_format == 'docx':
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif output_format == 'txt':
                mime_type = 'text/plain'
            elif output_format == 'md':
                mime_type = 'text/markdown'
            elif output_format == 'html':
                mime_type = 'text/html'
        
        # Send the response
        response = make_response(file_data)
        response.headers['Content-Type'] = mime_type or 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{output_filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up files in case of error
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up files: {str(cleanup_error)}")
        
        return jsonify({'error': 'An error occurred during conversion. Please try again.'}), 500

def determine_file_type(input_format, output_format):
    """Determine file type based on input and output formats."""
    audio_formats = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
    image_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
    document_formats = ['pdf', 'docx', 'txt', 'md', 'html']
    
    if input_format in audio_formats and output_format in audio_formats:
        return 'audio'
    elif input_format in image_formats and output_format in image_formats:
        return 'image'
    elif input_format in document_formats and output_format in document_formats:
        return 'document'
    else:
        return None

@app.context_processor
def utility_processor():
    """Add utility functions to Jinja2 context."""
    def get_conversion_count():
        if current_user.is_authenticated:
            return Conversion.query.filter_by(user_id=current_user.id).count()
        return 0
    
    return dict(get_conversion_count=get_conversion_count)

@app.route('/privacy')
def privacy_policy():
    return render_template('legal/privacy.html')

@app.route('/terms')
def terms_of_service():
    return render_template('legal/terms.html')

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=app.config['DEBUG'])