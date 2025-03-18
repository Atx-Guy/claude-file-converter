# services/ocr_service.py
import os
import logging
import tempfile
import shutil

logger = logging.getLogger(__name__)

class OCRService:
    """Service for OCR (Optical Character Recognition) operations."""
    
    def __init__(self, temp_dir='temp'):
        """Initialize OCR service with temporary directory for processing."""
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        self.has_tesseract = self._check_tesseract()
    
    def _check_tesseract(self):
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            return True
        except ImportError:
            logger.warning("pytesseract is not installed. OCR functionality will be limited.")
            return False
    
    def perform_ocr(self, input_path, output_format='pdf', language='eng'):
        """
        Perform OCR on an image or PDF file.
        
        Args:
            input_path (str): Path to the input file
            output_format (str): Output format ('pdf' or 'txt')
            language (str): OCR language code
        
        Returns:
            str: Path to the OCR result file
        """
        if not self.has_tesseract:
            logger.warning("OCR attempted but Tesseract is not available")
            # Create a simple output file indicating OCR is not available
            if output_format == 'txt':
                output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}.txt")
                with open(output_path, 'w') as f:
                    f.write("OCR is not available. Please install pytesseract.")
                return output_path
            else:
                # Just copy the original file for PDF format
                output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}")
                shutil.copy(input_path, output_path)
                return output_path
        
        try:
            import pytesseract
            from PIL import Image
            
            # Check if input is PDF or image
            is_pdf = input_path.lower().endswith('.pdf')
            
            if is_pdf:
                # For PDFs, we need to convert to images first
                try:
                    import fitz  # PyMuPDF
                    pdf = fitz.open(input_path)
                    
                    # Process each page
                    text_results = []
                    for page_num in range(len(pdf)):
                        page = pdf.load_page(page_num)
                        pix = page.get_pixmap()
                        
                        # Save as temporary image
                        img_path = os.path.join(self.temp_dir, f"ocr_temp_{page_num}.png")
                        pix.save(img_path)
                        
                        # Perform OCR on the image
                        text = pytesseract.image_to_string(Image.open(img_path), lang=language)
                        text_results.append(text)
                        
                        # Clean up
                        os.remove(img_path)
                    
                    # Create output based on format
                    if output_format == 'txt':
                        output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}.txt")
                        with open(output_path, 'w') as f:
                            f.write('\n\n'.join(text_results))
                    else:  # PDF
                        # Create a searchable PDF
                        from fpdf import FPDF
                        output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}")
                        pdf_out = FPDF()
                        for text in text_results:
                            pdf_out.add_page()
                            pdf_out.set_font("Arial", size=12)
                            pdf_out.multi_cell(0, 10, text)
                        pdf_out.output(output_path)
                
                except ImportError:
                    logger.warning("PyMuPDF not available for PDF processing")
                    # Fall back to processing just the first page
                    try:
                        from pdf2image import convert_from_path
                        images = convert_from_path(input_path, first_page=1, last_page=1)
                        text = pytesseract.image_to_string(images[0], lang=language)
                        
                        if output_format == 'txt':
                            output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}.txt")
                            with open(output_path, 'w') as f:
                                f.write(text)
                        else:
                            # Just copy the original PDF as we can't create a searchable PDF without PyMuPDF
                            output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}")
                            shutil.copy(input_path, output_path)
                    
                    except ImportError:
                        logger.warning("pdf2image not available for PDF processing")
                        # No PDF conversion libraries, return a message
                        output_path = os.path.join(self.temp_dir, "ocr_error.txt")
                        with open(output_path, 'w') as f:
                            f.write("PDF OCR requires either PyMuPDF or pdf2image.")
            
            else:
                # Process a single image
                text = pytesseract.image_to_string(Image.open(input_path), lang=language)
                
                if output_format == 'txt':
                    output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}.txt")
                    with open(output_path, 'w') as f:
                        f.write(text)
                else:
                    # Create a PDF with the text
                    from fpdf import FPDF
                    output_path = os.path.join(self.temp_dir, f"ocr_result_{os.path.basename(input_path)}.pdf")
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, text)
                    pdf.output(output_path)
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            # Create an error output file
            output_path = os.path.join(self.temp_dir, "ocr_error.txt")
            with open(output_path, 'w') as f:
                f.write(f"OCR processing error: {str(e)}")
            return output_path