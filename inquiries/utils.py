import os
from datetime import timedelta
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from django.core.exceptions import ValidationError

def extract_audio_duration(file_path):
    """
    Extract duration from audio/video files using mutagen library
    Returns duration in seconds as float
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return None
            
        # Get file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        print(f"Processing file: {file_path} (extension: {file_extension})")
        
        # Handle different file types
        if file_extension in ['.mp3']:
            audio = MP3(file_path)
            duration = audio.info.length if audio.info else None
            print(f"MP3 duration: {duration}")
            return duration
            
        elif file_extension in ['.wav']:
            audio = WAVE(file_path)
            duration = audio.info.length if audio.info else None
            print(f"WAV duration: {duration}")
            return duration
            
        elif file_extension in ['.ogg']:
            audio = OggVorbis(file_path)
            duration = audio.info.length if audio.info else None
            print(f"OGG duration: {duration}")
            return duration
            
        elif file_extension in ['.m4a', '.aac', '.mp4', '.avi', '.mov']:
            # Try to get duration using mutagen's generic File class
            audio = File(file_path)
            if audio and hasattr(audio.info, 'length'):
                duration = audio.info.length
                print(f"Generic audio/video duration: {duration}")
                return duration
            print(f"No duration info found for {file_extension} file")
            return None
            
        else:
            print(f"Unsupported file type: {file_extension}")
            return None
            
    except Exception as e:
        print(f"Error extracting duration from {file_path}: {str(e)}")
        return None

def format_duration(seconds):
    """
    Convert seconds to timedelta object
    """
    if seconds is None:
        return None
    return timedelta(seconds=seconds)

def get_duration_display(duration):
    """
    Return duration in a readable format (HH:MM:SS or MM:SS)
    """
    if not duration:
        return "Unknown"
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}" 