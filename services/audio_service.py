# Modified services/audio_service.py to handle missing dependencies

import os
import subprocess
import logging
import platform
import requests
import zipfile
import shutil
import tempfile

# Import handling for pydub with graceful fallback
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    # Create a simple stub class for AudioSegment to avoid errors
    class AudioSegment:
        @staticmethod
        def from_file(*args, **kwargs):
            raise ImportError("pydub.AudioSegment is not available. Missing dependencies: audioop/pyaudioop")
        
        @staticmethod
        def empty():
            """Return an empty audio segment"""
            raise ImportError("pydub.AudioSegment is not available. Missing dependencies: audioop/pyaudioop")

logger = logging.getLogger(__name__)

class AudioService:
    """Service for audio conversion operations."""
    
    def __init__(self, temp_dir='temp', ffmpeg_dir='ffmpeg-static'):
        """Initialize audio service with temporary directory for processing."""
        self.temp_dir = temp_dir
        self.ffmpeg_dir = ffmpeg_dir
        self.features_available = self._check_features()
        
        # Create directories
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(ffmpeg_dir, exist_ok=True)
        
        # Set up FFmpeg path
        self.ffmpeg_path = self._get_ffmpeg_path()
    
    def _check_features(self):
        """Check which audio features are available"""
        features = {
            "pydub": PYDUB_AVAILABLE,
            "ffmpeg": self._is_ffmpeg_installed()
        }
        
        logger.info(f"Audio service features: {features}")
        return features
    
    def _get_ffmpeg_path(self):
        """Get or download FFmpeg executable path."""
        # Check if FFmpeg is already available in the system
        if self._is_ffmpeg_installed():
            logger.info("System FFmpeg found")
            return 'ffmpeg'
        
        # Check if we have a downloaded FFmpeg
        ffmpeg_binary = self._get_ffmpeg_binary_path()
        if os.path.exists(ffmpeg_binary):
            logger.info(f"Using downloaded FFmpeg binary: {ffmpeg_binary}")
            return ffmpeg_binary
        
        # Download FFmpeg
        return self._download_ffmpeg()
    
    def _is_ffmpeg_installed(self):
        """Check if FFmpeg is installed on the system."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=False)
            return True
        except Exception:
            return False
    
    def _get_ffmpeg_binary_path(self):
        """Get FFmpeg binary path based on platform."""
        system = platform.system()
        if system == 'Windows':
            return os.path.join(self.ffmpeg_dir, 'ffmpeg.exe')
        else:  # Linux, Darwin
            return os.path.join(self.ffmpeg_dir, 'ffmpeg')
    
    def _download_ffmpeg(self):
        """Download FFmpeg for the current platform."""
        system = platform.system()
        
        if system == 'Windows':
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            binary_path = os.path.join(self.ffmpeg_dir, 'ffmpeg.exe')
        elif system == 'Darwin':  # macOS
            ffmpeg_url = "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
            binary_path = os.path.join(self.ffmpeg_dir, 'ffmpeg')
        else:  # Linux
            ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
            binary_path = os.path.join(self.ffmpeg_dir, 'ffmpeg')
        
        # Download and extract FFmpeg
        try:
            logger.info(f"Downloading FFmpeg from {ffmpeg_url}")
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                with requests.get(ffmpeg_url, stream=True) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                
                tmp_file_path = tmp_file.name
            
            # Extract downloaded archive
            extract_dir = tempfile.mkdtemp()
            
            if system == 'Windows' or system == 'Darwin':
                with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:  # Linux
                import tarfile
                with tarfile.open(tmp_file_path) as tar:
                    tar.extractall(extract_dir)
            
            # Find and move the FFmpeg binary
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file == 'ffmpeg' or file == 'ffmpeg.exe':
                        source_path = os.path.join(root, file)
                        shutil.move(source_path, binary_path)
                        os.chmod(binary_path, 0o755)  # Make executable
                        break
            
            # Clean up
            os.unlink(tmp_file_path)
            shutil.rmtree(extract_dir)
            
            logger.info(f"FFmpeg installed at {binary_path}")
            return binary_path
            
        except Exception as e:
            logger.error(f"Error downloading FFmpeg: {str(e)}")
            raise
    
    def convert_audio(self, input_path, output_path, options=None):
        """
        Convert an audio file using FFmpeg.
        
        Args:
            input_path (str): Path to the input audio file
            output_path (str): Path where the converted audio will be saved
            options (dict, optional): Additional conversion options
        
        Returns:
            str: Path to the converted audio file
        """
        try:
            # Check if we can use pydub for conversion
            if not self.features_available["pydub"]:
                logger.warning("pydub is not available, falling back to direct FFmpeg usage")
                return self._convert_with_ffmpeg(input_path, output_path, options)
            
            # Ensure paths are absolute
            input_path = os.path.abspath(input_path)
            output_path = os.path.abspath(output_path)
            
            # Get output format from file extension
            output_format = output_path.split('.')[-1].lower()
            
            logger.info(f"Converting {input_path} to {output_path} (format: {output_format})")
            
            # Set default options if not provided
            if options is None:
                options = {}
            
            # Use pydub for common audio conversions
            audio = AudioSegment.from_file(input_path)
            
            # Apply volume adjustment if specified
            if 'volume' in options:
                audio = audio.apply_gain(options['volume'])
            
            # Apply normalize if specified
            if options.get('normalize', False):
                audio = audio.normalize()
            
            # Apply fade in/out if specified
            if 'fade_in' in options:
                audio = audio.fade_in(int(options['fade_in'] * 1000))
            
            if 'fade_out' in options:
                audio = audio.fade_out(int(options['fade_out'] * 1000))
            
            # Apply channel conversion if specified
            if 'channels' in options:
                audio = audio.set_channels(options['channels'])
            
            # Apply sample rate conversion if specified
            if 'sample_rate' in options:
                audio = audio.set_frame_rate(options['sample_rate'])
            
            # For complex conversions or specific codecs, use FFmpeg directly
            if ('codec' in options or 'bitrate' in options or 
                output_format in ['m4a', 'aac', 'flac']):
                # Export to a temporary file with format matching input
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}")
                audio.export(temp_file.name, format=output_format)
                temp_file.close()
                
                # Use FFmpeg for final conversion with all options
                return self._convert_with_ffmpeg(temp_file.name, output_path, options)
            else:
                # For simple conversions, use pydub directly
                audio.export(
                    output_path,
                    format=output_format,
                    bitrate=f"{options.get('bitrate', 192)}k" if 'bitrate' in options else None
                )
            
            logger.info("Conversion successful")
            return output_path
            
        except ImportError:
            # Fall back to FFmpeg if pydub fails
            logger.warning("pydub operation failed, falling back to direct FFmpeg usage")
            return self._convert_with_ffmpeg(input_path, output_path, options)
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            raise

    def _convert_with_ffmpeg(self, input_path, output_path, options=None):
        """Convert audio using FFmpeg directly."""
        if options is None:
            options = {}
            
        # Prepare FFmpeg command
        command = [
            self.ffmpeg_path,
            '-y',  # Overwrite output if exists
            '-i', input_path,  # Input file
        ]
        
        # Add codec parameter if specified
        if 'codec' in options:
            command.extend(['-acodec', options['codec']])
        
        # Add bitrate parameter if specified
        if 'bitrate' in options:
            command.extend(['-b:a', f"{options['bitrate']}k"])
            
        # Add sample rate parameter if specified
        if 'sample_rate' in options:
            command.extend(['-ar', str(options['sample_rate'])])
            
        # Add channels parameter if specified
        if 'channels' in options:
            command.extend(['-ac', str(options['channels'])])
        
        # Get output format from file extension
        output_format = output_path.split('.')[-1].lower()
        
        # Format-specific options
        if output_format == 'mp3':
            if 'codec' not in options:
                command.extend(['-acodec', 'libmp3lame'])
            if 'bitrate' not in options:
                command.extend(['-b:a', '192k'])
        
        elif output_format == 'aac' or output_format == 'm4a':
            if 'codec' not in options:
                command.extend(['-acodec', 'aac'])
            if 'bitrate' not in options:
                command.extend(['-b:a', '192k'])
        
        elif output_format == 'ogg':
            if 'codec' not in options:
                command.extend(['-acodec', 'libvorbis'])
            if 'bitrate' not in options:
                command.extend(['-q:a', '4'])
        
        elif output_format == 'flac':
            if 'codec' not in options:
                command.extend(['-acodec', 'flac'])
        
        # Add output file to command
        command.append(output_path)
        
        # Run FFmpeg command
        logger.info(f"Running FFmpeg command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("FFmpeg conversion successful")
        return output_path

    def get_audio_info(self, file_path):
        """
        Get information about an audio file.
        
        Args:
            file_path (str): Path to the audio file
        
        Returns:
            dict: Audio information (duration, bitrate, etc.)
        """
        try:
            command = [
                self.ffmpeg_path,
                '-i', file_path
            ]
            
            # FFmpeg outputs to stderr, not stdout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the output
            info = {}
            output = result.stderr
            
            # Extract duration
            import re
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', output)
            if duration_match:
                h, m, s = duration_match.groups()
                info['duration'] = float(h) * 3600 + float(m) * 60 + float(s)
            
            # Extract bitrate
            bitrate_match = re.search(r'bitrate: (\d+) kb/s', output)
            if bitrate_match:
                info['bitrate'] = int(bitrate_match.group(1))
            
            # Extract audio stream info
            audio_match = re.search(r'Stream.*Audio: (.*)', output)
            if audio_match:
                audio_info = audio_match.group(1)
                
                # Extract codec
                codec_match = re.search(r'^(\w+)', audio_info)
                if codec_match:
                    info['codec'] = codec_match.group(1)
                
                # Extract sample rate
                sample_rate_match = re.search(r'(\d+) Hz', audio_info)
                if sample_rate_match:
                    info['sample_rate'] = int(sample_rate_match.group(1))
                
                # Extract channels
                channels_match = re.search(r'(mono|stereo|(\d+) channels)', audio_info)
                if channels_match:
                    if channels_match.group(1) == 'mono':
                        info['channels'] = 1
                    elif channels_match.group(1) == 'stereo':
                        info['channels'] = 2
                    else:
                        info['channels'] = int(channels_match.group(2))
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            raise
            
    # Other methods remain mostly the same but with appropriate error handling...