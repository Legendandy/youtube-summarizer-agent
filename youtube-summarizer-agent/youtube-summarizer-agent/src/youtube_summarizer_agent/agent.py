from sentient_agent_framework import (
    AbstractAgent,
    Session,
    Query,
    ResponseHandler
)

from .utils import URLParser
from .transcript_service import TranscriptService
from .summarizer_service import SummarizerService
from .response_generator import ResponseGenerator
from utils.cache import CacheManager
from utils.security import SecurityValidator
from utils.rate_limiter import RateLimiter


class YouTubeSummarizerAgent(AbstractAgent):
    """Main agent class that orchestrates video summarization"""
    
    def __init__(self):
        """Initialize agent with all required services"""
        super().__init__("YouTube Summarizer")
        
        # Initialize services
        self.url_parser = URLParser()
        self.transcript_service = TranscriptService()
        self.summarizer_service = SummarizerService()
        self.response_generator = ResponseGenerator()
        
        # Initialize utilities
        self.cache_manager = CacheManager(cache_dir=".cache", ttl_hours=168)  # 7 days
        self.security_validator = SecurityValidator()
        self.rate_limiter = RateLimiter(
            requests_per_minute=10,
            requests_per_hour=50,
            max_concurrent_platform=200,
            cooldown_seconds=0,  # No cooldown between requests
            block_duration_seconds=300
        )
    
    def _get_user_id(self, session: Session) -> str:
        """
        Extracts unique user identifier from session
        
        Args:
            session: Session object from framework
            
        Returns:
            Unique user identifier
        """
        # Use session ID as user identifier
        # In production, you might use authenticated user IDs
        return session.session_id if hasattr(session, 'session_id') else "anonymous"
    
    def _is_greeting_or_identity(self, prompt: str) -> tuple[bool, str]:
        """
        Checks if prompt is a greeting or identity question
        
        Args:
            prompt: User's input prompt
            
        Returns:
            Tuple of (is_greeting, prompt_type)
        """
        lower_prompt = prompt.lower().strip()
        
        identity_prompts = [
            'who are you', 'what do you do', 'what are you',
            'who are you?', 'what do you do?', 'what are you?'
        ]
        
        greeting_prompts = [
            'hi', 'hello', 'hey', 'hi!', 'hello!', 'hey!'
        ]
        
        if lower_prompt in identity_prompts:
            return True, "identity"
        elif lower_prompt in greeting_prompts:
            return True, "greeting"
        
        return False, ""
    
    async def assist(self, session: Session, query: Query, response_handler: ResponseHandler):
        """
        Main assist method - processes user queries
        
        Args:
            session: Current session object
            query: User's query
            response_handler: Handler for streaming responses
        """
        user_id = self._get_user_id(session)
        
        try:
            # Security validation
            is_safe, security_error = self.security_validator.validate(query.prompt)
            if not is_safe:
                await self.response_generator.stream_security_error(
                    response_handler, 
                    security_error
                )
                await response_handler.complete()
                return
            
            # Check for greeting/identity queries (NO rate limiting for these)
            is_greeting, prompt_type = self._is_greeting_or_identity(query.prompt)
            if is_greeting:
                await self.response_generator.stream_greeting(
                    response_handler, 
                    prompt_type
                )
                await response_handler.complete()
                return
            
            # Extract YouTube URL
            youtube_url = self.url_parser.find_youtube_url(query.prompt)
            
            # If no YouTube URL, respond with general message (NO rate limiting)
            if not youtube_url:
                await self.response_generator.stream_greeting(
                    response_handler, 
                    "general"
                )
                await response_handler.complete()
                return
            
            # Rate limiting check - ONLY for video summarization
            is_allowed, rate_limit_error = await self.rate_limiter.acquire(user_id)
            if not is_allowed:
                await self.response_generator.stream_rate_limit_error(
                    response_handler,
                    rate_limit_error
                )
                await response_handler.complete()
                return
            
            try:
                
                # Extract video ID
                video_id = self.url_parser.extract_youtube_video_id(youtube_url)
                
                if not video_id:
                    await self.response_generator.stream_invalid_url_error(response_handler)
                    await response_handler.complete()
                    return
                
                # Check cache first
                cached_summary = self.cache_manager.get(video_id)
                
                if cached_summary:
                    await response_handler.emit_text_block(
                        "STATUS", "Transcript extracted successfully. Generating summary..."
                    )
                    
                    final_response_stream = response_handler.create_text_stream("FINAL_RESPONSE")
                    
                    # Stream cached summary with natural typing speed
                    import asyncio
                    summary_text = cached_summary.get('summary', '')
                    for char in summary_text:
                        await final_response_stream.emit_chunk(char)
                        await asyncio.sleep(0.003)  # Same speed as fresh generation
                    
                    await final_response_stream.complete()
                    await response_handler.complete()
                    return
                
                # Extract transcript
                await response_handler.emit_text_block(
                    "STATUS", "Thinking about your query..."
                )
                
                transcript_result = await self.transcript_service.get_youtube_transcript(video_id)
                
                if not transcript_result["success"]:
                    clean_error = self.transcript_service.parse_error(
                        transcript_result['error']
                    )
                    await self.response_generator.stream_transcript_error(
                        response_handler,
                        clean_error
                    )
                    await response_handler.complete()
                    return
                
                # Generate summary
                await response_handler.emit_text_block(
                    "STATUS", "Transcript extracted successfully. Generating summary..."
                )
                
                final_response_stream = response_handler.create_text_stream("FINAL_RESPONSE")
                
                await final_response_stream.emit_chunk("")
                
                # Collect summary for caching
                summary_parts = []
                
                try:
                    async for chunk in self.summarizer_service.summarize_stream(
                        transcript_result["transcript_with_timestamps"],
                        transcript_result["transcript_data"]
                    ):
                        await final_response_stream.emit_chunk(chunk)
                        summary_parts.append(chunk)
                except Exception as e:
                    error_msg = f"\n\nError: {str(e)}"
                    await final_response_stream.emit_chunk(error_msg)
                    summary_parts.append(error_msg)
                
                footer = f"\n\n---\n*Summarized from: {youtube_url}*"
                await final_response_stream.emit_chunk(footer)
                summary_parts.append(footer)
                
                await final_response_stream.complete()
                
                # Cache the summary
                full_summary = "".join(summary_parts)
                self.cache_manager.set(
                    video_id,
                    full_summary,
                    metadata={'url': youtube_url}
                )
                
                await response_handler.complete()
            
            finally:
                # Always release rate limiter slot
                await self.rate_limiter.release()
        
        except Exception as e:
            # Handle unexpected errors
            await self.response_generator.stream_error(
                response_handler,
                "Unexpected Error",
                f"An unexpected error occurred: {str(e)}\n\nPlease try again later."
            )
            await response_handler.complete()
            
            # Release rate limiter slot on error
            await self.rate_limiter.release()