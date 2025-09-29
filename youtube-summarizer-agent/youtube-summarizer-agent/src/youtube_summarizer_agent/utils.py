import re
from typing import Optional


class URLParser:
    """Handles YouTube URL parsing and validation"""
    
    @staticmethod
    def extract_youtube_video_id(url: str) -> Optional[str]:
        """
        Extracts video ID from YouTube URL
        
        Args:
            url: YouTube URL
            
        Returns:
            11-character video ID or None if not found
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def find_youtube_url(text: str) -> Optional[str]:
        """
        Finds YouTube URL in text
        
        Args:
            text: Text that may contain a YouTube URL
            
        Returns:
            YouTube URL or None if not found
        """
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?[^\s]+',
            r'https?://(?:www\.)?youtu\.be/[^\s]+',
            r'https?://(?:www\.)?youtube\.com/embed/[^\s]+',
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None