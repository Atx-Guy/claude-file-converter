# models/conversion.py
from models import db
from datetime import datetime

class Conversion(db.Model):
    """Model for tracking conversion history."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation = db.Column(db.String(50), nullable=False)
    input_filename = db.Column(db.String(255), nullable=False)
    output_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('conversions', lazy=True))
    
    def __repr__(self):
        return f'<Conversion {self.operation} {self.created_at}>'
    
    @property
    def operation_display_name(self):
        """Return a human-readable operation name."""
        operation_names = {
            'convert_audio': 'Audio Conversion',
            'convert_image': 'Image Conversion',
            'convert_document': 'Document Conversion',
            'pdf_split': 'PDF Split',
            'pdf_split_multiple': 'PDF Split (Multiple)',
            'pdf_merge': 'PDF Merge',
            'pdf_compress': 'PDF Compression',
            'pdf_protect': 'PDF Protection',
            'pdf_unlock': 'PDF Unlock',
            'pdf_rotate': 'PDF Rotation',
            'pdf_watermark': 'PDF Watermark',
            'pdf_to_image': 'PDF to Image',
            'pdf_to_images': 'PDF to Images',
            'images_to_pdf': 'Images to PDF',
            'pdf_ocr': 'PDF OCR'
        }
        return operation_names.get(self.operation, self.operation.replace('_', ' ').title())
    
    @property
    def icon_class(self):
        """Return an appropriate icon class based on operation."""
        icon_mapping = {
            'convert_audio': 'bi-music-note',
            'convert_image': 'bi-image',
            'convert_document': 'bi-file-text',
            'pdf_split': 'bi-scissors',
            'pdf_split_multiple': 'bi-scissors',
            'pdf_merge': 'bi-front',
            'pdf_compress': 'bi-file-zip',
            'pdf_protect': 'bi-shield-lock',
            'pdf_unlock': 'bi-unlock',
            'pdf_rotate': 'bi-arrow-clockwise',
            'pdf_watermark': 'bi-badge-cc',
            'pdf_to_image': 'bi-file-earmark-image',
            'pdf_to_images': 'bi-images',
            'images_to_pdf': 'bi-file-earmark-pdf',
            'pdf_ocr': 'bi-textarea-t'
        }
        return icon_mapping.get(self.operation, 'bi-gear')