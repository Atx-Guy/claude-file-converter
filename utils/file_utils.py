# utils/file_utils.py
import os
import uuid
import logging
import mimetypes
import magic  # python-magic library for better MIME type detection

logger = logging.getLogger(__name__)

def create_temp_directory(directory_path):
    """Create a temporary directory if it doesn't exist."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Temporary directory created/verified: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating temporary directory: {str(e)}")
        return False

def get_file_extension(filename):
    """Extract file extension from filename."""
    if not filename:
        return ''
    return os.path.splitext(filename)[1][1:].lower()

def allowed_file(filename, allowed_extensions):
    """Check if a file is allowed based on its extension."""
    return '.' in filename and get_file_extension(filename) in allowed_extensions

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension."""
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id

def get_mime_type(file_path):
    """
    Get MIME type of a file using python-magic for more accurate detection.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: MIME type of the file
    """
    try:
        # Use python-magic for more accurate MIME type detection
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except Exception as e:
        logger.warning(f"Error detecting MIME type with python-magic: {str(e)}")
        # Fallback to mimetypes library
        return mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

def get_file_size_formatted(file_path):
    """
    Get formatted file size.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: Formatted file size (e.g., "2.5 MB")
    """
    try:
        size_bytes = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                break
            size_bytes /= 1024
        
        return f"{size_bytes:.2f} {unit}"
    except Exception as e:
        logger.error(f"Error getting file size: {str(e)}")
        return "Unknown size"

def clean_temp_files(directory_path, exclude_files=None):
    """
    Clean temporary files from a directory.
    
    Args:
        directory_path (str): Path to the directory
        exclude_files (list, optional): List of files to exclude from cleaning
    
    Returns:
        int: Number of files deleted
    """
    if exclude_files is None:
        exclude_files = []
    
    if not os.path.exists(directory_path):
        return 0
    
    count = 0
    try:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            # Skip excluded files and directories
            if filename in exclude_files or not os.path.isfile(file_path):
                continue
            
            # Delete file
            os.remove(file_path)
            count += 1
            
        logger.info(f"Cleaned {count} temporary files from {directory_path}")
        return count
    except Exception as e:
        logger.error(f"Error cleaning temporary files: {str(e)}")
        return 0

def save_uploaded_file(file, directory, filename=None, allowed_extensions=None):
    """
    Save an uploaded file to the specified directory.
    
    Args:
        file: Flask FileStorage object
        directory (str): Directory where the file will be saved
        filename (str, optional): Custom filename, otherwise generate a unique name
        allowed_extensions (set, optional): Set of allowed file extensions
    
    Returns:
        str: Path to the saved file, or None if save failed
    """
    if not file:
        return None
    
    # Check if file type is allowed
    original_filename = file.filename
    if allowed_extensions and not allowed_file(original_filename, allowed_extensions):
        logger.warning(f"File type not allowed: {original_filename}")
        return None
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            filename = generate_unique_filename(original_filename)
        
        # Create full file path
        file_path = os.path.join(directory, filename)
        
        # Save file
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        return None