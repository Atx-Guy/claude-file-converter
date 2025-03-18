# tests/test_pdf_service.py
import os
import unittest
import tempfile
from services.pdf_service import PDFService

class TestPDFService(unittest.TestCase):
    """Test cases for PDFService."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_service = PDFService(temp_dir=self.temp_dir)
        
        # Create a simple test PDF
        self.test_pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n')
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_split_pdf(self):
        """Test splitting a PDF."""
        # Test with a valid page range
        page_ranges = ['1']
        output_paths = self.pdf_service.split_pdf(self.test_pdf_path, page_ranges)
        
        self.assertEqual(len(output_paths), 1)
        self.assertTrue(os.path.exists(output_paths[0]))
    
    def test_merge_pdfs(self):
        """Test merging PDFs."""
        # Create a second test PDF
        test_pdf2_path = os.path.join(self.temp_dir, 'test2.pdf')
        with open(test_pdf2_path, 'wb') as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n')
        
        # Test merging
        input_paths = [self.test_pdf_path, test_pdf2_path]
        output_path = self.pdf_service.merge_pdfs(input_paths)
        
        self.assertTrue(os.path.exists(output_path))
    
    def test_compress_pdf(self):
        """Test compressing a PDF."""
        output_path = self.pdf_service.compress_pdf(self.test_pdf_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        # Check that file size is not larger than original
        self.assertLessEqual(os.path.getsize(output_path), 
                           os.path.getsize(self.test_pdf_path) * 1.1)  # Allow 10% overhead

# More test cases would be added for other services