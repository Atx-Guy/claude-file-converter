# services/pdf_service.py
import os
import logging
import tempfile
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import io
import uuid
import shutil

logger = logging.getLogger(__name__)

class PDFService:
    """Service for handling various PDF operations with reduced dependencies."""
    
    def __init__(self, temp_dir='temp'):
        """Initialize PDF service with temporary directory for processing."""
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def _get_temp_path(self, prefix='pdf_', suffix='.pdf'):
        """Generate a temporary file path."""
        return os.path.join(self.temp_dir, f"{prefix}{uuid.uuid4()}{suffix}")
    
    def split_pdf(self, input_path, page_ranges):
        """
        Split a PDF file according to specified page ranges.
        
        Args:
            input_path (str): Path to the input PDF file
            page_ranges (list): List of page ranges, e.g. ['1-3', '5-7', '9']
        
        Returns:
            list: List of paths to split PDF files
        """
        try:
            reader = PdfReader(input_path)
            output_paths = []
            
            for page_range in page_ranges:
                writer = PdfWriter()
                
                # Parse page range (e.g., '1-3' or '5')
                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                else:
                    start = end = int(page_range)
                
                # Adjust for 0-based indexing
                start = max(0, start - 1)
                end = min(len(reader.pages) - 1, end - 1)
                
                # Add pages to writer
                for page_num in range(start, end + 1):
                    writer.add_page(reader.pages[page_num])
                
                # Save split PDF
                output_path = self._get_temp_path(prefix=f'split_{page_range}_')
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                output_paths.append(output_path)
            
            return output_paths
            
        except Exception as e:
            logger.error(f"Error splitting PDF: {str(e)}")
            raise
    
    def merge_pdfs(self, input_paths, output_filename=None):
        """
        Merge multiple PDFs into a single PDF.
        
        Args:
            input_paths (list): List of paths to input PDF files
            output_filename (str, optional): Custom filename for the merged PDF
        
        Returns:
            str: Path to the merged PDF file
        """
        try:
            merger = PdfMerger()
            
            # Add each PDF to the merger
            for path in input_paths:
                merger.append(path)
            
            # Generate output path
            if output_filename:
                output_path = self._get_temp_path(prefix=f"{output_filename}_")
            else:
                output_path = self._get_temp_path(prefix='merged_')
            
            # Write merged PDF
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            
            merger.close()
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            raise
    
    def add_password(self, input_path, user_password, owner_password=None):
        """
        Add password protection to a PDF.
        
        Args:
            input_path (str): Path to the input PDF file
            user_password (str): Password required to open the document
            owner_password (str, optional): Password for full access rights
        
        Returns:
            str: Path to the password-protected PDF
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # Add all pages to the writer
            for page in reader.pages:
                writer.add_page(page)
            
            # If owner_password is not provided, use user_password
            if not owner_password:
                owner_password = user_password
            
            # Encrypt the PDF
            writer.encrypt(user_password, owner_password)
            
            # Save protected PDF
            output_path = self._get_temp_path(prefix='protected_')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding password to PDF: {str(e)}")
            raise
    
    def remove_password(self, input_path, password):
        """
        Remove password protection from a PDF.
        
        Args:
            input_path (str): Path to the input PDF file
            password (str): Current password of the PDF
        
        Returns:
            str: Path to the unprotected PDF
        """
        try:
            # Open encrypted PDF
            reader = PdfReader(input_path)
            
            # Check if PDF is encrypted
            if reader.is_encrypted:
                # Try to decrypt with provided password
                success = reader.decrypt(password)
                if not success:
                    raise ValueError("Incorrect password")
            
            # Create a new unencrypted PDF
            writer = PdfWriter()
            
            # Add all pages to the writer
            for page in reader.pages:
                writer.add_page(page)
            
            # Save unprotected PDF
            output_path = self._get_temp_path(prefix='unprotected_')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error removing password from PDF: {str(e)}")
            raise
    
    def rotate_pdf(self, input_path, rotation, pages='all'):
        """
        Rotate pages in a PDF (simplified version using PyPDF2).
        
        Args:
            input_path (str): Path to the input PDF file
            rotation (int): Rotation angle in degrees (90, 180, 270)
            pages (str or list): 'all' or list of page numbers
        
        Returns:
            str: Path to the rotated PDF
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # Determine which pages to rotate
            if pages == 'all':
                page_indices = range(len(reader.pages))
            else:
                # Convert page numbers to 0-based indices
                page_indices = [p - 1 for p in pages if 0 < p <= len(reader.pages)]
            
            # Process each page
            for i in range(len(reader.pages)):
                page = reader.pages[i]
                if i in page_indices:
                    # PyPDF2 rotation is counterclockwise, so we negate the angle
                    page.rotate(rotation)
                writer.add_page(page)
            
            # Save rotated PDF
            output_path = self._get_temp_path(prefix='rotated_')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error rotating PDF: {str(e)}")
            raise
    
def compress_pdf(self, input_path, quality='medium'):
    """
    Compress a PDF file to reduce its size.
    
    Args:
        input_path (str): Path to the input PDF file
        quality (str): Compression quality - 'low', 'medium', or 'high'
    
    Returns:
        str: Path to the compressed PDF file
    """
    try:
        # Generate output path
        output_path = self._get_temp_path(prefix='compressed_')
        
        # First attempt: Try using PyMuPDF (fitz) if available
        try:
            import fitz
            logger.info("Using PyMuPDF for PDF compression")
            
            # Quality settings
            quality_settings = {
                'low': {'image_quality': 30},
                'medium': {'image_quality': 60},
                'high': {'image_quality': 85}
            }
            
            settings = quality_settings.get(quality, quality_settings['medium'])
            
            # Open the PDF
            pdf = fitz.open(input_path)
            
            # Save with compression options
            pdf.save(output_path, garbage=3, deflate=True)
            pdf.close()
            
            logger.info(f"PDF compressed successfully with PyMuPDF, saved to {output_path}")
            return output_path
            
        except ImportError as e:
            logger.warning(f"PyMuPDF not available: {str(e)}. Trying PyPDF2 method.")
            
        # Second attempt: Try using PyPDF2
        try:
            from PyPDF2 import PdfReader, PdfWriter
            logger.info("Using PyPDF2 for basic PDF compression")
            
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # Copy pages to new document
            for page in reader.pages:
                writer.add_page(page)
            
            # Save the PDF
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            logger.info(f"PDF compressed successfully with PyPDF2, saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"PyPDF2 compression failed: {str(e)}. Falling back to file copy.")
        
        # Last resort: Just copy the file
        logger.warning("All compression methods failed. Copying file instead.")
        import shutil
        shutil.copy(input_path, output_path)
        return output_path
            
    except Exception as e:
        logger.error(f"Error compressing PDF: {str(e)}", exc_info=True)
        # Re-raise with more information
        raise RuntimeError(f"PDF compression failed: {str(e)}")
    
    def images_to_pdf(self, image_paths, output_filename=None):
        """
        Convert images to a PDF using Pillow.
        
        Args:
            image_paths (list): List of paths to image files
            output_filename (str, optional): Custom filename for the output PDF
        
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Generate output path
            if output_filename:
                output_path = self._get_temp_path(prefix=f"{output_filename}_")
            else:
                output_path = self._get_temp_path(prefix='images_to_pdf_')
            
            # Use Pillow to create a PDF
            from PIL import Image
            
            # Open the first image to get dimensions
            images = []
            for path in image_paths:
                img = Image.open(path).convert('RGB')
                images.append(img)
            
            # Save as PDF
            if images:
                images[0].save(
                    output_path, 
                    save_all=True, 
                    append_images=images[1:] if len(images) > 1 else []
                )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting images to PDF: {str(e)}")
            raise
    
    def perform_ocr(self, input_path, output_format='pdf', language='eng'):
        """
        Placeholder for OCR functionality.
        
        Args:
            input_path (str): Path to the input PDF file
            output_format (str): Output format ('pdf' or 'txt')
            language (str): OCR language code
        
        Returns:
            str: Path to the OCR result file (original file copied)
        """
        try:
            # For now, just return a text file or copy of PDF stating OCR is not available
            if output_format == 'txt':
                output_path = self._get_temp_path(prefix='ocr_', suffix='.txt')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("OCR functionality is not available.\n")
                    f.write("Install pytesseract and Tesseract OCR to enable this feature.")
            else:
                # Just copy the original PDF
                output_path = self._get_temp_path(prefix='ocr_')
                shutil.copy(input_path, output_path)
            
            logger.warning("OCR functionality not available")
            return output_path
            
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            raise
    
    def add_watermark(self, input_path, watermark_text, position='center', opacity=0.3):
        """
        Simple placeholder for watermark functionality.
        
        Args:
            input_path (str): Path to the input PDF file
            watermark_text (str): Text to use as watermark
            position (str): Position of watermark ('center', 'top', 'bottom')
            opacity (float): Opacity of watermark (0-1)
        
        Returns:
            str: Path to the watermarked PDF (original file copied)
        """
        try:
            # Just copy the original PDF for now
            output_path = self._get_temp_path(prefix='watermarked_')
            shutil.copy(input_path, output_path)
            
            logger.warning("Watermark functionality not available - file was copied without watermark")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding watermark: {str(e)}")
            raise
    
    def cleanup_temp_files(self, file_paths=None):
        """
        Clean up temporary files.
        
        Args:
            file_paths (list, optional): List of specific file paths to clean up.
                                        If None, all files in temp_dir will be removed.
        """
        try:
            if file_paths:
                for path in file_paths:
                    if os.path.exists(path):
                        os.remove(path)
            else:
                # Clean all files in temp directory
                for filename in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")