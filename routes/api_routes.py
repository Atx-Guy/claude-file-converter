# routes/api_routes.py
import os
import logging
import json
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.conversion import Conversion
from services.audio_service import AudioService
from services.image_service import ImageService
from services.document_service import DocumentService
from services.pdf_service import PDFService
from utils.file_utils import allowed_file, get_file_extension, save_uploaded_file
import traceback
import io

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize services
audio_service = AudioService()
image_service = ImageService()
document_service = DocumentService()
pdf_service = PDFService()

@api_bp.route('/info', methods=['GET'])
def api_info():
    """Get API information."""
    return jsonify({
        'name': 'File Converter API',
        'version': '1.0.0',
        'description': 'API for file conversion operations',
        'endpoints': [
            {
                'path': '/api/info',
                'method': 'GET',
                'description': 'Get API information'
            },
            {
                'path': '/api/convert',
                'method': 'POST',
                'description': 'Convert a file from one format to another'
            },
            {
                'path': '/api/pdf/split',
                'method': 'POST',
                'description': 'Split a PDF file into multiple files'
            },
            {
                'path': '/api/pdf/merge',
                'method': 'POST',
                'description': 'Merge multiple PDF files into a single file'
            },
            {
                'path': '/api/pdf/compress',
                'method': 'POST',
                'description': 'Compress a PDF file'
            },
            {
                'path': '/api/pdf/protect',
                'method': 'POST',
                'description': 'Add password protection to a PDF file'
            }
        ]
    })

@api_bp.route('/convert', methods=['POST'])
def api_convert():
    """Convert a file from one format to another."""
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No selected file'}), 400
    
    # Get output format
    output_format = request.form.get('output_format')
    if not output_format:
        return jsonify({'error': 'Output format not specified'}), 400
    
    # Get original filename without extension
    original_filename = os.path.splitext(file.filename)[0]
    input_format = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    # Get custom filename if provided
    custom_filename = request.form.get('output_filename')
    if custom_filename and custom_filename.strip():
        output_filename = f"{custom_filename}.{output_format}"
    else:
        output_filename = f"{original_filename}.{output_format}"
    
    # Create temp paths
    temp_dir = current_app.config['TEMP_FOLDER']
    input_path = os.path.join(temp_dir, f"api_input_{secure_filename(file.filename)}")
    output_path = os.path.join(temp_dir, f"api_output_{secure_filename(output_filename)}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Determine file type and convert
        conversion_type = request.form.get('type') or determine_file_type(input_format, output_format)
        
        if not conversion_type:
            return jsonify({'error': 'Could not determine conversion type'}), 400
        
        if conversion_type == 'audio':
            # Parse audio options
            options = {}
            if 'options' in request.form:
                try:
                    options = json.loads(request.form.get('options'))
                except json.JSONDecodeError:
                    pass
            
            # Convert audio
            audio_service.convert_audio(input_path, output_path, options)
            operation = 'convert_audio'
            
        elif conversion_type == 'image':
            # Parse image options
            options = {}
            if 'options' in request.form:
                try:
                    options = json.loads(request.form.get('options'))
                except json.JSONDecodeError:
                    pass
            
            # Convert image
            image_service.convert_image(input_path, output_path, options)
            operation = 'convert_image'
            
        elif conversion_type == 'document':
            # Convert document
            document_service.convert_document(input_path, output_path)
            operation = 'convert_document'
            
        else:
            return jsonify({'error': 'Unsupported conversion type'}), 400
        
        # Record conversion for authenticated users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation=operation,
                input_filename=file.filename,
                output_filename=output_filename
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Return the converted file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        logger.error(f"API conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

@api_bp.route('/pdf/split', methods=['POST'])
def api_pdf_split():
    """Split a PDF file into multiple files."""
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    # Get page ranges
    page_ranges = request.form.get('page_ranges')
    if not page_ranges:
        return jsonify({'error': 'Page ranges not specified'}), 400
    
    # Parse page ranges
    try:
        page_ranges = [range.strip() for range in page_ranges.split(',')]
    except Exception:
        return jsonify({'error': 'Invalid page ranges format'}), 400
    
    # Create temp paths
    temp_dir = current_app.config['TEMP_FOLDER']
    input_path = os.path.join(temp_dir, f"api_input_{secure_filename(file.filename)}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Split PDF
        output_paths = pdf_service.split_pdf(input_path, page_ranges)
        
        # Record conversion for authenticated users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation='pdf_split',
                input_filename=file.filename,
                output_filename='split_pages.zip'
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Create ZIP file for multiple outputs
        if len(output_paths) > 1:
            import zipfile
            zip_path = os.path.join(temp_dir, 'split_pages.zip')
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for i, path in enumerate(output_paths):
                    zip_file.write(path, f"split_part_{i+1}.pdf")
            
            # Return the ZIP file
            return send_file(
                zip_path,
                as_attachment=True,
                download_name='split_pages.zip'
            )
        else:
            # Return the single file
            return send_file(
                output_paths[0],
                as_attachment=True,
                download_name='split.pdf'
            )
        
    except Exception as e:
        logger.error(f"API PDF split error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            for path in output_paths:
                if os.path.exists(path):
                    os.remove(path)
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

@api_bp.route('/pdf/merge', methods=['POST'])
def api_pdf_merge():
    """Merge multiple PDF files into a single file."""
    # Check if files are present
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    if len(files) < 2:
        return jsonify({'error': 'At least two PDF files are required'}), 400
    
    # Create temp directory
    temp_dir = current_app.config['TEMP_FOLDER']
    input_paths = []
    
    try:
        # Save uploaded files
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                input_path = os.path.join(temp_dir, f"api_input_{secure_filename(file.filename)}")
                file.save(input_path)
                input_paths.append(input_path)
        
        if len(input_paths) < 2:
            return jsonify({'error': 'At least two valid PDF files are required'}), 400
        
        # Get output filename
        output_filename = request.form.get('output_filename', 'merged.pdf')
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
        
        # Merge PDFs
        output_path = pdf_service.merge_pdfs(input_paths)
        
        # Record conversion for authenticated users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation='pdf_merge',
                input_filename=','.join([f.filename for f in files]),
                output_filename=output_filename
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Return the merged file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        logger.error(f"API PDF merge error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up files
        try:
            for path in input_paths:
                if os.path.exists(path):
                    os.remove(path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

@api_bp.route('/pdf/compress', methods=['POST'])
def api_pdf_compress():
    """Compress a PDF file."""
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    # Get compression quality
    quality = request.form.get('quality', 'medium')
    if quality not in ['low', 'medium', 'high']:
        quality = 'medium'
    
    # Create temp paths
    temp_dir = current_app.config['TEMP_FOLDER']
    input_path = os.path.join(temp_dir, f"api_input_{secure_filename(file.filename)}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Compress PDF
        output_path = pdf_service.compress_pdf(input_path, quality)
        
        # Get output filename
        output_filename = request.form.get('output_filename', f"compressed_{os.path.basename(file.filename)}")
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
        
        # Record conversion for authenticated users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation='pdf_compress',
                input_filename=file.filename,
                output_filename=output_filename
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Return the compressed file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        logger.error(f"API PDF compress error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

@api_bp.route('/pdf/protect', methods=['POST'])
def api_pdf_protect():
    """Add password protection to a PDF file."""
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    # Get passwords
    user_password = request.form.get('user_password')
    owner_password = request.form.get('owner_password')
    
    if not user_password:
        return jsonify({'error': 'User password is required'}), 400
    
    # Create temp paths
    temp_dir = current_app.config['TEMP_FOLDER']
    input_path = os.path.join(temp_dir, f"api_input_{secure_filename(file.filename)}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Protect PDF
        output_path = pdf_service.add_password(input_path, user_password, owner_password)
        
        # Get output filename
        output_filename = request.form.get('output_filename', f"protected_{os.path.basename(file.filename)}")
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
        
        # Record conversion for authenticated users
        if current_user.is_authenticated:
            conversion = Conversion(
                user_id=current_user.id,
                operation='pdf_protect',
                input_filename=file.filename,
                output_filename=output_filename
            )
            db.session.add(conversion)
            db.session.commit()
        
        # Return the protected file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        logger.error(f"API PDF protect error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Clean up files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")

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