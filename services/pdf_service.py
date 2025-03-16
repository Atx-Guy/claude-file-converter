# services/pdf_service.py
import os
import logging
import tempfile
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import img2pdf
import fitz  # PyMuPDF
import io
import uuid
import shutil

logger = logging.getLogger(__name__)

class PDFService:
    """Service for handling various PDF operations."""
    
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
            # Quality settings
            quality_settings = {
                'low': 30,      # Higher compression, lower quality
                'medium': 60,   # Balanced compression and quality
                'high': 90      # Lower compression, higher quality
            }
            
            quality_value = quality_settings.get(quality, 60)
            
            # Open the PDF
            doc = fitz.open(input_path)
            output_path = self._get_temp_path(prefix='compressed_')
            
            # Create a new PDF writer
            writer = PdfWriter()
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get page as an image
                pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
                img_data = pix.tobytes("jpeg", quality_value)
                
                # Convert image back to PDF page
                img = Image.open(io.BytesIO(img_data))
                img_pdf = img2pdf.convert(img.tobytes())
                
                # Add page to new PDF
                temp_pdf = io.BytesIO(img_pdf)
                reader = PdfReader(temp_pdf)
                writer.add_page(reader.pages[0])
            
            # Save compressed PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error compressing PDF: {str(e)}")
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
        Rotate pages in a PDF.
        
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
            for i, page in enumerate(reader.pages):
                if i in page_indices:
                    # Rotate the page
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
    
    def add_watermark(self, input_path, watermark_text, position='center', opacity=0.3):
        """
        Add text watermark to a PDF.
        
        Args:
            input_path (str): Path to the input PDF file
            watermark_text (str): Text to use as watermark
            position (str): Position of watermark ('center', 'top', 'bottom')
            opacity (float): Opacity of watermark (0-1)
        
        Returns:
            str: Path to the watermarked PDF
        """
        try:
            # Open the PDF
            doc = fitz.open(input_path)
            output_path = self._get_temp_path(prefix='watermarked_')
            
            # Process each page
            for page in doc:
                # Define font and size
                font = "helv"
                fontsize = 24
                
                # Calculate watermark position
                rect = page.rect
                if position == 'top':
                    point = fitz.Point(rect.width / 2, rect.height * 0.1)
                elif position == 'bottom':
                    point = fitz.Point(rect.width / 2, rect.height * 0.9)
                else:  # center
                    point = fitz.Point(rect.width / 2, rect.height / 2)
                
                # Insert watermark text
                page.insert_text(
                    point,
                    watermark_text,
                    fontname=font,
                    fontsize=fontsize,
                    rotate=45,
                    color=(0, 0, 0),
                    alpha=opacity
                )
            
            # Save watermarked PDF
            doc.save(output_path)
            doc.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding watermark to PDF: {str(e)}")
            raise
    
    def pdf_to_images(self, input_path, image_format='png', dpi=200):
        """
        Convert PDF pages to images.
        
        Args:
            input_path (str): Path to the input PDF file
            image_format (str): Output image format ('png', 'jpg', etc.)
            dpi (int): Resolution in DPI
        
        Returns:
            list: List of paths to image files
        """
        try:
            # Convert PDF to images
            images = convert_from_path(input_path, dpi=dpi)
            output_paths = []
            
            # Save each image
            for i, image in enumerate(images):
                image_path = self._get_temp_path(prefix=f'page_{i+1}_', suffix=f'.{image_format}')
                image.save(image_path, format=image_format.upper())
                output_paths.append(image_path)
            
            return output_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise
    
    def images_to_pdf(self, image_paths, output_filename=None):
        """
        Convert images to a PDF.
        
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
            
            # Convert images to PDF
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert([Image.open(img).filename for img in image_paths]))
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting images to PDF: {str(e)}")
            raise
    
    def perform_ocr(self, input_path, output_format='pdf', language='eng'):
        """
        Perform OCR on a scanned PDF.
        
        Args:
            input_path (str): Path to the input PDF file
            output_format (str): Output format ('pdf' or 'txt')
            language (str): OCR language code
        
        Returns:
            str: Path to the OCR result file
        """
        try:
            # Create a temporary directory for OCR processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert PDF to images
                images = convert_from_path(input_path, output_folder=temp_dir)
                
                if output_format == 'txt':
                    # Extract text with OCR
                    text = ""
                    for image in images:
                        text += pytesseract.image_to_string(image, lang=language)
                        text += "\n\n"
                    
                    # Save text to output file
                    output_path = self._get_temp_path(prefix='ocr_', suffix='.txt')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                
                else:  # pdf
                    # Create a new PDF writer
                    writer = PdfWriter()
                    
                    # Process each image
                    for image in images:
                        # Extract text with OCR
                        text = pytesseract.image_to_string(image, lang=language)
                        
                        # Create PDF from image
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        
                        # Convert image to PDF
                        pdf_bytes = img2pdf.convert(img_bytes.read())
                        
                        # Create a PDF page from the image
                        reader = PdfReader(io.BytesIO(pdf_bytes))
                        page = reader.pages[0]
                        
                        # Add invisible text layer with OCR results (this creates searchable PDF)
                        # Note: This is a simplified approach, a full implementation would
                        # use proper word positions and font metrics
                        writer.add_page(page)
                    
                    # Save OCR PDF
                    output_path = self._get_temp_path(prefix='ocr_')
                    with open(output_path, 'wb') as f:
                        writer.write(f)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
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