# services/document_service.py
import os
import logging
import shutil

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for document conversion operations with reduced dependencies."""
    
    def __init__(self, temp_dir='temp'):
        """Initialize document service with temporary directory for processing."""
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def convert_document(self, input_path, output_path):
        """
        Simple document conversion using basic text handling.
        
        Args:
            input_path (str): Path to the input document file
            output_path (str): Path where the converted document will be saved
        """
        input_format = input_path.split('.')[-1].lower()
        output_format = output_path.split('.')[-1].lower()
        
        logger.info(f"Converting document from {input_format} to {output_format}")
        
        try:
            if input_format == 'txt' and output_format == 'txt':
                # Just copy the file
                shutil.copy(input_path, output_path)
                
            elif input_format == 'txt' and output_format == 'html':
                # Convert TXT to basic HTML
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                html_content = "<html><body>"
                for line in content.split('\n'):
                    if line.strip():
                        html_content += f"<p>{line}</p>\n"
                html_content += "</body></html>"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
            elif input_format == 'html' and output_format == 'txt':
                # Convert HTML to TXT using BeautifulSoup
                try:
                    from bs4 import BeautifulSoup
                    
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text(separator='\n')
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                except ImportError:
                    # Fallback: simple HTML to text conversion
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Very basic HTML tag removal
                    import re
                    text = re.sub(r'<[^>]+>', '', content)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
            
            elif input_format == 'md' and output_format in ('html', 'txt'):
                # Convert Markdown to HTML or TXT
                try:
                    import markdown
                    
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if output_format == 'html':
                        html_content = markdown.markdown(content)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(f"<html><body>\n{html_content}\n</body></html>")
                    else:  # txt
                        # Convert markdown to HTML, then to plain text
                        html_content = markdown.markdown(content)
                        
                        # Simple HTML tag removal
                        import re
                        text = re.sub(r'<[^>]+>', '', html_content)
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(text)
                except ImportError:
                    logger.warning("Markdown module not available - copying file without conversion")
                    shutil.copy(input_path, output_path)
            
            elif input_format == 'pdf' and output_format == 'txt':
                # Convert PDF to text using PyPDF2
                try:
                    from PyPDF2 import PdfReader
                    
                    reader = PdfReader(input_path)
                    text = ""
                    
                    for page in reader.pages:
                        text += page.extract_text() + "\n\n"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    # Create a placeholder text file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write("PDF text extraction failed. Please install PyPDF2 or pdfminer.six for this feature.")
            
            elif input_format == 'pdf' and output_format in ('html', 'docx'):
                # Placeholder - can't convert PDF to HTML/DOCX without additional libraries
                logger.warning(f"Conversion from PDF to {output_format} requires additional libraries")
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    if output_format == 'html':
                        f.write("<html><body><p>PDF to HTML conversion requires additional libraries.</p></body></html>")
                    else:
                        # Create a simple text file with .docx extension
                        f.write("PDF to DOCX conversion requires additional libraries.")
            
            else:
                logger.warning(f"Unsupported conversion: {input_format} to {output_format}")
                # Just copy the file and change extension
                shutil.copy(input_path, output_path)
                
        except Exception as e:
            logger.error(f"Document conversion error: {str(e)}")
            raise