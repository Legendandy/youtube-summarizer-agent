import os
from dotenv import load_dotenv

load_dotenv()


class YouTubeConfig:
    """Configuration for YouTube transcript extraction"""
    
    # Proxy configuration for YouTube Transcript API
    PROXY_USERNAME = os.getenv("YOUTUBE_PROXY_USERNAME", "bckefkmt-rotate")
    PROXY_PASSWORD = os.getenv("YOUTUBE_PROXY_PASSWORD", "klne0rjlnila")
    
    # Transcript settings
    DEFAULT_LANGUAGE = "en"
    TRANSCRIPT_TIMEOUT = 30.0  # seconds
    
    # Supported YouTube URL patterns
    URL_PATTERNS = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    @classmethod
    def get_proxy_config(cls):
        """Returns proxy configuration dict"""
        return {
            "proxy_username": cls.PROXY_USERNAME,
            "proxy_password": cls.PROXY_PASSWORD
        }