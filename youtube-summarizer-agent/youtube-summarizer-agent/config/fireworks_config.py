import os
from dotenv import load_dotenv

load_dotenv()


class FireworksConfig:
    """Configuration for Fireworks AI summarization"""
    
    # API credentials
    API_KEY = os.getenv("FIREWORKS_API_KEY")
    
    # API endpoints
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Model configuration
    MODEL = "x-ai/grok-4-fast:free"
    MAX_TOKENS = 2048
    TEMPERATURE = 0.3
    TOP_P = 0.9
    
    # Request settings
    TIMEOUT = 60.0  # seconds
    STREAM = True
    
    @classmethod
    def validate(cls):
        """Validates that required configuration is present"""
        if not cls.API_KEY:
            raise ValueError("FIREWORKS_API_KEY environment variable is required")
        return True
    
    @classmethod
    def get_headers(cls):
        """Returns API request headers"""
        return {
            "Authorization": f"Bearer {cls.API_KEY}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def get_payload(cls, messages, stream=None):
        """Returns API request payload"""
        return {
            "model": cls.MODEL,
            "messages": messages,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
            "top_p": cls.TOP_P,
            "stream": stream if stream is not None else cls.STREAM
        }