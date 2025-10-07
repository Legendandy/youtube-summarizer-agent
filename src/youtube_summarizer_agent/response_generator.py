import asyncio
import random
from sentient_agent_framework import ResponseHandler


class ResponseGenerator:
    """Generates and streams responses to users"""
    
    # Greeting responses for different prompt types
    IDENTITY_RESPONSES = [
        "Hello! I'm a YouTube Summarizer Agent specialized in analyzing YouTube videos and creating detailed summaries with timestamps. Share a YouTube URL and I'll break it down for you!",
        "Hi there! I'm designed to summarize YouTube videos with comprehensive breakdowns and timestamps. Got a video you'd like me to analyze?",
        "I'm a YouTube video analysis agent! I create detailed summaries of YouTube content with section breakdowns and timestamps. Drop a YouTube link and let's get started!",
        "Hey! I specialize in turning YouTube videos into structured summaries with timestamps and key insights. Have a video you need summarized?"
    ]
    
    GREETING_RESPONSES = [
        "Hello! I specialize in summarizing YouTube videos. If you have a YouTube video link you'd like me to analyze, I'd be happy to create a detailed summary for you!",
        "Hi there! I'm here to help you understand YouTube videos better through detailed summaries. Share a YouTube URL and I'll get to work!",
        "Hey! I turn YouTube videos into comprehensive summaries with timestamps. Got a video you need broken down?",
        "Hello! I analyze YouTube content and create structured summaries. Drop a YouTube link and I'll provide you with a detailed breakdown!"
    ]
    
    GENERAL_RESPONSES = [
        "I specialize in YouTube video analysis and summarization. While I can't help with general questions, I'd love to summarize any YouTube video you share!",
        "I'm focused on creating detailed YouTube video summaries. For other topics, you might want to try a different agent, but I'm great with YouTube content!",
        "My expertise is in analyzing and summarizing YouTube videos with timestamps and breakdowns. Got a video link you'd like me to work on?"
    ]
    
    @staticmethod
    def get_greeting_response(prompt_type: str) -> str:
        """
        Gets a random greeting response based on prompt type
        
        Args:
            prompt_type: Type of greeting ("identity", "greeting", or "general")
            
        Returns:
            Appropriate greeting message
        """
        if prompt_type == "identity":
            return random.choice(ResponseGenerator.IDENTITY_RESPONSES)
        elif prompt_type == "greeting":
            return random.choice(ResponseGenerator.GREETING_RESPONSES)
        else:
            return random.choice(ResponseGenerator.GENERAL_RESPONSES)
    
    @staticmethod
    async def stream_greeting(response_handler: ResponseHandler, prompt_type: str):
        """
        Streams a greeting response with typing effect
        
        Args:
            response_handler: Response handler from framework
            prompt_type: Type of greeting to display
        """
        await response_handler.emit_text_block(
            "STATUS", "Thinking about your query..."
        )
        
        response = ResponseGenerator.get_greeting_response(prompt_type)
        
        greeting_stream = response_handler.create_text_stream("GREETING_RESPONSE")
        
        for char in response:
            await greeting_stream.emit_chunk(char)
            await asyncio.sleep(0.01)
        
        await greeting_stream.complete()
    
    @staticmethod
    async def stream_error(response_handler: ResponseHandler, error_message: str, details: str = ""):
        """
        Streams an error message to user
        
        Args:
            response_handler: Response handler from framework
            error_message: Main error message
            details: Additional error details (optional)
        """
        await response_handler.emit_text_block(
            "STATUS", "Thinking about your query..."
        )
        
        error_stream = response_handler.create_text_stream("ERROR_RESPONSE")
        
        full_message = f" **{error_message}**\n\n{details}" if details else f" **{error_message}**"
        
        for char in full_message:
            await error_stream.emit_chunk(char)
            await asyncio.sleep(0.005)
        
        await error_stream.complete()
    
    @staticmethod
    async def stream_invalid_url_error(response_handler: ResponseHandler):
        """Streams error for invalid YouTube URL"""
        error_details = """**This could be due to:**
- Malformed or incomplete YouTube URL
- Missing characters in the video ID
- URL format not recognized

**Please:**
- Double-check the YouTube URL is correct and complete
- Ensure the full video ID is included (11 characters)

**Valid YouTube URL formats:**
- https://youtube.com/watch?v=VIDEO_ID
- https://youtu.be/VIDEO_ID
- https://youtube.com/embed/VIDEO_ID"""
        
        await ResponseGenerator.stream_error(
            response_handler,
            "Invalid YouTube URL",
            error_details
        )
    
    @staticmethod
    async def stream_transcript_error(response_handler: ResponseHandler, clean_error: str):
        """
        Streams error for transcript extraction failure
        
        Args:
            response_handler: Response handler from framework
            clean_error: Cleaned error message
        """
        error_details = f"""

**This could be due to:**
- Video doesn't have English captions/subtitles
- Video is private or age restricted 
- Captions are disabled

**Please try:**
- A different video with English captions
- Ensuring the video is publicly accessible
- Waiting a moment and trying again"""
        
        await ResponseGenerator.stream_error(
            response_handler,
            "Failed to extract transcript from video",
            error_details
        )
    
    @staticmethod
    async def stream_security_error(response_handler: ResponseHandler, error_message: str):
        """
        Streams security validation error
        
        Args:
            response_handler: Response handler from framework
            error_message: Security error message
        """
        error_details = """

**For your security:**
- Malicious patterns were detected in your input
- Please revise your request and try again
- If you believe this is an error, please contact support"""
        
        await ResponseGenerator.stream_error(
            response_handler,
            f"Security Alert: {error_message}",
            error_details
        )
    
    @staticmethod
    async def stream_rate_limit_error(response_handler: ResponseHandler, error_message: str):
        """
        Streams rate limit error
        
        Args:
            response_handler: Response handler from framework
            error_message: Rate limit error message
        """
        await ResponseGenerator.stream_error(
            response_handler,
            "Rate Limit Exceeded",
            f"\n{error_message}\n\nPlease wait before making another request."
        )