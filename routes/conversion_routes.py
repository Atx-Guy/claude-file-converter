# routes/conversion_routes.py
import os
import logging
import mimetypes
from flask import Blueprint, request, render_template, send_file, jsonify, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.conversion import Conversion
from services.audio_service import AudioService
from services.image_service import ImageService
from services.document_service import DocumentService
from utils.file_utils import allowed_file, get_file_extension, save_uploaded_file
import traceback
import io
import zipfile

logger = logging.getLogger(__name__)
conversion_bp = Blueprint('conversion', __name__, url_prefix='/convert')

# Initialize services
audio_service = AudioService()
image_service = ImageService()
document_service = DocumentService()

@conversion_bp.route('/', methods=['GET'])
def conversion_home():
    """Show the general conversion page or redirect to specific conversion type."""
    conversion_type = request.args.get('type', 'general')
    if conversion_type in ['general', 'audio', 'image', 'document']:
        return render_template(f'convert/{conversion_type}.html')
    return render_template('convert/general.html')

@conversion_bp.route('/file', methods=['POST'])
def convert_file():
    """Handle single file conversion."""
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
    
    # Create temp directory if it doesn't exist
    temp_dir = current_app.config['TEMP_FOLDER']
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save uploaded file to temp directory
    input_path = os.path.join(temp_dir, f"temp_input.{input_format}")
    output_path = os.path.join(temp_dir, f"temp_output.{output_format}")
    
    try:
        # Save uploaded file
        file.save(input_path)
        
        # Determine file type and use appropriate service
        file_type = determine_file_type(input_format, output_format)
        
        if file_type == 'audio':
            # Parse audio options
            options = parse_audio_options(request.form)
            
            # Convert audio file
            logger.info(f"Converting audio from {input_format} to {output_format}")
            audio_service.convert_audio(input_path, output_path, options)
            operation = 'convert_audio'
            
        elif file_type == 'image':
            # Parse image options
            options = parse_image_options(request.form)
            
            # Convert image file
            logger.info(f"Converting image from {input_format} to {output_format}")
            image_service.convert_image(input_path, output_path, options)
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


@conversion_bp.route('/batch', methods=['POST'])
def batch_convert():
    """Handle batch file conversion."""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    conversion_type = request.form.get('conversion_type')
    if conversion_type not in ['audio', 'image', 'document']:
        return jsonify({'error': 'Invalid conversion type'}), 400
    
    # Get output format based on conversion type
    output_format = None
    if conversion_type == 'audio':
        output_format = request.form.get('audio_format')
    elif conversion_type == 'image':
        output_format = request.form.get('image_format')
    elif conversion_type == 'document':
        output_format = request.form.get('document_format')
    
    if not output_format:
        return jsonify({'error': 'Output format not specified'}), 400
    
    # Create temporary directories
    temp_dir = current_app.config['TEMP_FOLDER']
    input_dir = os.path.join(temp_dir, 'batch_input')
    output_dir = os.path.join(temp_dir, 'batch_output')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare to track converted files
    converted_files = []
    errors = []
    
    try:
        # Process each file
        for file in files:
            if not file.filename:
                continue
            
            input_format = get_file_extension(file.filename)
            original_filename = os.path.splitext(file.filename)[0]
            
            # Set output filename
            prefix = request.form.get('output_prefix', '')
            output_filename = f"{prefix}{original_filename}.{output_format}"
            
            # Save input file
            input_path = os.path.join(input_dir, secure_filename(file.filename))
            output_path = os.path.join(output_dir, secure_filename(output_filename))
            
            file.save(input_path)
            
            try:
                # Convert file based on type
                if conversion_type == 'audio':
                    options = parse_audio_options(request.form)
                    audio_service.convert_audio(input_path, output_path, options)
                    
                elif conversion_type == 'image':
                    options = parse_image_options(request.form)
                    image_service.convert_image(input_path, output_path, options)
                    
                elif conversion_type == 'document':
                    document_service.convert_document(input_path, output_path)
                
                # Add to converted files
                converted_files.append({
                    'original': file.filename,
                    'converted': output_filename,
                    'path': output_path
                })
                
                # Record conversion for logged in users
                if current_user.is_authenticated:
                    conversion = Conversion(
                        user_id=current_user.id,
                        operation=f'convert_{conversion_type}',
                        input_filename=file.filename,
                        output_filename=output_filename
                    )
                    db.session.add(conversion)
            
            except Exception as e:
                logger.error(f"Error converting {file.filename}: {str(e)}")
                errors.append({
                    'file': file.filename,
                    'error': str(e)
                })
        
        # Commit conversions to database
        if current_user.is_authenticated:
            db.session.commit()
        
        # Prepare response
        if len(converted_files) == 0:
            return jsonify({
                'success': False,
                'message': 'No files were converted successfully',
                'errors': errors
            }), 400
        
        # Create ZIP if requested or if multiple files
        download_as_zip = request.form.get('download_as_zip') == 'true' or len(converted_files) > 1
        
        if download_as_zip:
            # Create ZIP file
            zip_path = os.path.join(temp_dir, 'batch_result.zip')
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for file_info in converted_files:
                    zip_file.write(file_info['path'], file_info['converted'])
            
            # Read ZIP file
            with open(zip_path, 'rb') as f:
                file_data = f.read()
            
            # Clean up
            try:
                os.remove(zip_path)
            except Exception as e:
                logger.error(f"Error removing ZIP file: {str(e)}")
            
            # Send ZIP response
            response = make_response(file_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename="converted_files.zip"'
            
        else:
            # Send single file
            file_info = converted_files[0]
            with open(file_info['path'], 'rb') as f:
                file_data = f.read()
            
            # Determine MIME type
            mime_type = mimetypes.guess_type(file_info['converted'])[0] or 'application/octet-stream'
            
            # Send response
            response = make_response(file_data)
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Disposition'] = f'attachment; filename="{file_info["converted"]}"'
        
        # Clean up
        for file_path in os.listdir(input_dir):
            try:
                os.remove(os.path.join(input_dir, file_path))
            except Exception:
                pass
        
        for file_path in os.listdir(output_dir):
            try:
                os.remove(os.path.join(output_dir, file_path))
            except Exception:
                pass
        
        return response
        
    except Exception as e:
        logger.error(f"Batch conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': 'An error occurred during batch conversion',
            'error': str(e)
        }), 500


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


def parse_audio_options(form_data):
    """Parse audio conversion options from form data."""
    options = {}
    
    # Parse bitrate
    if 'bitrate' in form_data:
        try:
            options['bitrate'] = int(form_data.get('bitrate'))
        except ValueError:
            pass
    
    # Parse sample rate
    if 'sample_rate' in form_data:
        try:
            options['sample_rate'] = int(form_data.get('sample_rate'))
        except ValueError:
            pass
    
    # Parse channels
    if 'channels' in form_data:
        try:
            options['channels'] = int(form_data.get('channels'))
        except ValueError:
            pass
    
    # Parse normalize
    if 'normalize' in form_data:
        options['normalize'] = form_data.get('normalize') == 'true'
    
    # Parse volume adjustment
    if 'volume' in form_data:
        try:
            options['volume'] = float(form_data.get('volume'))
        except ValueError:
            pass
    
    # Parse fade in/out
    if 'fade_in' in form_data:
        try:
            options['fade_in'] = float(form_data.get('fade_in'))
        except ValueError:
            pass
    
    if 'fade_out' in form_data:
        try:
            options['fade_out'] = float(form_data.get('fade_out'))
        except ValueError:
            pass
    
    return options


def parse_image_options(form_data):
    """Parse image conversion options from form data."""
    options = {}
    
    # Parse quality
    if 'quality' in form_data:
        try:
            options['quality'] = int(form_data.get('quality'))
        except ValueError:
            pass
    
    # Parse resize
    if 'resize' in form_data and form_data.get('resize') == 'true':
        width = None
        height = None
        
        if 'width' in form_data:
            try:
                width = int(form_data.get('width'))
            except ValueError:
                pass
        
        if 'height' in form_data:
            try:
                height = int(form_data.get('height'))
            except ValueError:
                pass
        
        if width or height:
            options['resize'] = (width, height)
    
    # Parse crop
    if 'crop' in form_data and form_data.get('crop') == 'true':
        try:
            left = int(form_data.get('crop_left', 0))
            top = int(form_data.get('crop_top', 0))
            right = int(form_data.get('crop_right', 0))
            bottom = int(form_data.get('crop_bottom', 0))
            options['crop'] = (left, top, right, bottom)
        except ValueError:
            pass
    
    # Parse rotate
    if 'rotate' in form_data:
        try:
            options['rotate'] = int(form_data.get('rotate'))
        except ValueError:
            pass
    
    # Parse flip
    if 'flip' in form_data:
        options['flip'] = form_data.get('flip')
    
    # Parse brightness
    if 'brightness' in form_data:
        try:
            options['brightness'] = float(form_data.get('brightness'))
        except ValueError:
            pass
    
    # Parse contrast
    if 'contrast' in form_data:
        try:
            options['contrast'] = float(form_data.get('contrast'))
        except ValueError:
            pass
    
    # Parse sharpness
    if 'sharpness' in form_data:
        try:
            options['sharpness'] = float(form_data.get('sharpness'))
        except ValueError:
            pass
    
    # Parse filter
    if 'filter' in form_data:
        options['filter'] = form_data.get('filter')
    
    return options