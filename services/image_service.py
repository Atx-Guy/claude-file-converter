# services/image_service.py
import os
import logging
from PIL import Image, ImageOps, ImageEnhance
import io

logger = logging.getLogger(__name__)

class ImageService:
    """Service for image conversion and processing operations."""
    
    def __init__(self, temp_dir='temp'):
        """Initialize image service with temporary directory for processing."""
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def convert_image(self, input_path, output_path, options=None):
        """
        Convert image to different format with optional processing.
        
        Args:
            input_path (str): Path to the input image file
            output_path (str): Path where the converted image will be saved
            options (dict, optional): Processing options like quality, resize, etc.
        """
        try:
            # Open the image
            img = Image.open(input_path)
            
            # Apply processing options if provided
            if options:
                img = self._apply_image_processing(img, options)
            
            # Convert RGBA to RGB if saving as JPEG
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format in ['.jpg', '.jpeg'] and img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                img = background
            
            # Set quality for JPG/JPEG
            save_kwargs = {}
            if output_format in ['.jpg', '.jpeg']:
                quality = options.get('quality', 95) if options else 95
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_format == '.png':
                save_kwargs['optimize'] = True
            elif output_format == '.webp':
                quality = options.get('quality', 90) if options else 90
                save_kwargs['quality'] = quality
            
            # Save the processed image
            img.save(output_path, **save_kwargs)
            
            logger.info(f"Image converted and saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting image: {str(e)}")
            raise
    
    def _apply_image_processing(self, img, options):
        """
        Apply various image processing operations.
        
        Args:
            img (PIL.Image): Image to process
            options (dict): Processing options
        
        Returns:
            PIL.Image: Processed image
        """
        # Resize
        if 'resize' in options:
            width, height = options['resize']
            if width and height:
                img = img.resize((width, height), Image.LANCZOS)
            elif width:
                # Calculate height to maintain aspect ratio
                wpercent = width / float(img.size[0])
                hsize = int(float(img.size[1]) * float(wpercent))
                img = img.resize((width, hsize), Image.LANCZOS)
            elif height:
                # Calculate width to maintain aspect ratio
                hpercent = height / float(img.size[1])
                wsize = int(float(img.size[0]) * float(hpercent))
                img = img.resize((wsize, height), Image.LANCZOS)
        
        # Crop
        if 'crop' in options:
            left, top, right, bottom = options['crop']
            img = img.crop((left, top, right, bottom))
        
        # Rotate
        if 'rotate' in options:
            angle = options['rotate']
            img = img.rotate(angle, expand=True, resample=Image.BICUBIC)
        
        # Flip
        if 'flip' in options:
            flip_mode = options['flip']
            if flip_mode == 'horizontal':
                img = ImageOps.mirror(img)
            elif flip_mode == 'vertical':
                img = ImageOps.flip(img)
        
        # Adjustments
        if 'brightness' in options:
            factor = options['brightness']
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(factor)
        
        if 'contrast' in options:
            factor = options['contrast']
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(factor)
        
        if 'sharpness' in options:
            factor = options['sharpness']
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(factor)
        
        # Filters
        if 'filter' in options:
            filter_type = options['filter']
            if filter_type == 'grayscale':
                img = ImageOps.grayscale(img)
            elif filter_type == 'sepia':
                img = self._apply_sepia(img)
            elif filter_type == 'negative':
                img = ImageOps.invert(img)
        
        return img
    
    def _apply_sepia(self, img):
        """Apply sepia filter to image."""
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to grayscale
        gray = ImageOps.grayscale(img)
        
        # Apply sepia tone
        result = Image.new('RGB', gray.size)
        for x in range(gray.width):
            for y in range(gray.height):
                gray_px = gray.getpixel((x, y))
                r = min(255, int(gray_px * 1.07))
                g = min(255, int(gray_px * 0.74))
                b = min(255, int(gray_px * 0.43))
                result.putpixel((x, y), (r, g, b))
        
        return result
    
    def batch_process_images(self, input_paths, output_dir, format, options=None):
        """
        Process multiple images with the same options.
        
        Args:
            input_paths (list): List of paths to input image files
            output_dir (str): Directory where converted images will be saved
            format (str): Output format (jpg, png, etc.)
            options (dict, optional): Processing options
        
        Returns:
            list: List of paths to converted images
        """
        os.makedirs(output_dir, exist_ok=True)
        
        output_paths = []
        for input_path in input_paths:
            try:
                # Generate output filename
                filename = os.path.basename(input_path)
                name, _ = os.path.splitext(filename)
                output_path = os.path.join(output_dir, f"{name}.{format}")
                
                # Convert image
                self.convert_image(input_path, output_path, options)
                output_paths.append(output_path)
                
            except Exception as e:
                logger.error(f"Error processing image {input_path}: {str(e)}")
                # Continue with other images even if one fails
        
        return output_paths
    
    def create_thumbnail(self, input_path, output_path, size=(200, 200)):
        """
        Create a thumbnail of an image.
        
        Args:
            input_path (str): Path to the input image file
            output_path (str): Path where the thumbnail will be saved
            size (tuple): Thumbnail size (width, height)
        
        Returns:
            str: Path to the generated thumbnail
        """
        try:
            # Open the image
            img = Image.open(input_path)
            
            # Create thumbnail
            img.thumbnail(size, Image.LANCZOS)
            
            # Convert RGBA to RGB if saving as JPEG
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format in ['.jpg', '.jpeg'] and img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                img = background
            
            # Save thumbnail
            img.save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            raise
    
    def add_watermark(self, input_path, output_path, watermark_text, position='center', opacity=0.5):
        """
        Add text watermark to an image.
        
        Args:
            input_path (str): Path to the input image file
            output_path (str): Path where the watermarked image will be saved
            watermark_text (str): Text to use as watermark
            position (str): Position of watermark ('center', 'topleft', etc.)
            opacity (float): Opacity of watermark (0-1)
        
        Returns:
            str: Path to the watermarked image
        """
        try:
            # Open the image
            img = Image.open(input_path)
            
            # Create a transparent text layer
            from PIL import ImageDraw, ImageFont
            
            # Create a blank image for the text
            txt = Image.new('RGBA', img.size, (255, 255, 255, 0))
            
            # Get a font
            try:
                font = ImageFont.truetype('arial.ttf', 36)
            except IOError:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get a drawing context
            d = ImageDraw.Draw(txt)
            
            # Calculate position
            w, h = d.textsize(watermark_text, font)
            x, y = 0, 0
            
            if position == 'center':
                x = (img.width - w) // 2
                y = (img.height - h) // 2
            elif position == 'topleft':
                x, y = 10, 10
            elif position == 'topright':
                x, y = img.width - w - 10, 10
            elif position == 'bottomleft':
                x, y = 10, img.height - h - 10
            elif position == 'bottomright':
                x, y = img.width - w - 10, img.height - h - 10
            
            # Draw text with semi-transparency
            d.text((x, y), watermark_text, fill=(0, 0, 0, int(255 * opacity)), font=font)
            
            # Combine the image with the watermark
            watermarked = Image.alpha_composite(img.convert('RGBA'), txt)
            
            # Convert RGBA to RGB if saving as JPEG
            output_format = os.path.splitext(output_path)[1].lower()
            if output_format in ['.jpg', '.jpeg']:
                watermarked = watermarked.convert('RGB')
            
            # Save the watermarked image
            watermarked.save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding watermark: {str(e)}")
            raise