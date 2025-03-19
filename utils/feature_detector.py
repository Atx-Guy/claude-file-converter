# utils/feature_detector.py
import importlib
import logging

logger = logging.getLogger(__name__)

class FeatureDetector:
    """Utility class to detect available features based on installed packages."""
    
    @staticmethod
    def check_package(package_name):
        """Check if a Python package is installed and can be imported."""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_pdf_features():
        """Detect available PDF processing features."""
        features = {
            'basic': True,  # Basic features using PyPDF2 are always available
            'advanced': False,  # Advanced features using reportlab/PyMuPDF
            'ocr': False,  # OCR features using pytesseract
            'html_rendering': False,  # HTML rendering (for PDF generation from HTML)
            'image_extraction': False,  # PDF to image extraction
        }
        
        # Check for reportlab (required for advanced PDF generation)
        if FeatureDetector.check_package('reportlab'):
            features['advanced'] = True
        
        # Check for PyMuPDF (used for advanced PDF manipulation)
        if FeatureDetector.check_package('fitz'):
            features['advanced'] = True
        
        # Check for pytesseract (required for OCR)
        if FeatureDetector.check_package('pytesseract'):
            features['ocr'] = True
        
        # Check for pdfkit/wkhtmltopdf (required for HTML to PDF)
        if FeatureDetector.check_package('pdfkit'):
            features['html_rendering'] = True
        
        # Check for pdf2image (required for PDF to image conversion)
        if FeatureDetector.check_package('pdf2image'):
            features['image_extraction'] = True
        
        return features
    
    @staticmethod
    def get_document_features():
        """Detect available document processing features."""
        features = {
            'basic': True,  # Basic text file handling is always available
            'markdown': False,  # Markdown processing
            'html': False,  # HTML processing
            'word': False,  # Word document processing
        }
        
        # Check for markdown (for Markdown processing)
        if FeatureDetector.check_package('markdown'):
            features['markdown'] = True
        
        # Check for lxml (required for advanced HTML processing)
        if FeatureDetector.check_package('lxml'):
            features['html'] = True
        elif FeatureDetector.check_package('bs4'):
            # BeautifulSoup without lxml can still do basic HTML processing
            features['html'] = True
        
        # Check for python-docx (required for Word document processing)
        if FeatureDetector.check_package('docx'):
            features['word'] = True
        
        return features
    
    @staticmethod
    def get_image_features():
        """Detect available image processing features."""
        features = {
            'basic': False,  # Basic image processing using Pillow
            'advanced': False,  # Advanced features
        }
        
        # Check for Pillow (required for basic image processing)
        if FeatureDetector.check_package('PIL'):
            features['basic'] = True
        
        return features
    
    @staticmethod
    def get_audio_features():
        """Detect available audio processing features."""
        features = {
            'basic': False,  # Basic audio processing using pydub
            'advanced': False,  # Advanced features requiring ffmpeg
        }
        
        # Check for pydub (required for basic audio processing)
        if FeatureDetector.check_package('pydub'):
            features['basic'] = True
        
        # Check for ffmpeg-python (required for advanced audio processing)
        if FeatureDetector.check_package('ffmpeg'):
            features['advanced'] = True
        
        return features