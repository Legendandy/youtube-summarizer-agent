import os
import re
import asyncio
import random
from typing import Dict, Any, List, Optional, AsyncIterator
import httpx
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api.formatters import TextFormatter
from sentient_agent_framework import (
    AbstractAgent,
    DefaultServer,
    Session,
    Query,
    ResponseHandler
)

# Load environment variables from .env file
load_dotenv()


class YouTubeSummarizerAgent(AbstractAgent):
    def __init__(self):
        super().__init__("YouTube Summarizer")
        self.fireworks_api_key = os.getenv("FIREWORKS_API_KEY")
        if not self.fireworks_api_key:
            raise ValueError("FIREWORKS_API_KEY environment variable is required")
        
        self.fireworks_base_url = "https://api.fireworks.ai/inference/v1/chat/completions"
        self.model = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    
    def extract_youtube_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def find_youtube_url(self, text: str) -> Optional[str]:
        """Find YouTube URL in the input text"""
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
    
    def get_greeting_response(self, prompt_type: str) -> str:
        """Generate varied responses for common queries"""
        
        identity_responses = [
            "Hello! I'm a YouTube Summarizer Agent specialized in analyzing YouTube videos and creating detailed summaries with timestamps. Share a YouTube URL and I'll break it down for you!",
            "Hi there! I'm designed to summarize YouTube videos with comprehensive breakdowns and timestamps. Got a video you'd like me to analyze?",
            "I'm a YouTube video analysis agent! I create detailed summaries of YouTube content with section breakdowns and timestamps. Drop a YouTube link and let's get started!",
            "Hey! I specialize in turning YouTube videos into structured summaries with timestamps and key insights. Have a video you need summarized?"
        ]
        
        greeting_responses = [
            "Hello! I specialize in summarizing YouTube videos. If you have a YouTube video link you'd like me to analyze, I'd be happy to create a detailed summary for you!",
            "Hi there! I'm here to help you understand YouTube videos better through detailed summaries. Share a YouTube URL and I'll get to work!",
            "Hey! I turn YouTube videos into comprehensive summaries with timestamps. Got a video you need broken down?",
            "Hello! I analyze YouTube content and create structured summaries. Drop a YouTube link and I'll provide you with a detailed breakdown!"
        ]
        
        general_responses = [
            "I specialize in YouTube video analysis and summarization. While I can't help with general questions, I'd love to summarize any YouTube video you share!",
            "I'm focused on creating detailed YouTube video summaries. For other topics, you might want to try a different agent, but I'm great with YouTube content!",
            "My expertise is in analyzing and summarizing YouTube videos with timestamps and breakdowns. Got a video link you'd like me to work on?"
        ]
        
        if prompt_type == "identity":
            return random.choice(identity_responses)
        elif prompt_type == "greeting":
            return random.choice(greeting_responses)
        else:
            return random.choice(general_responses)
    
    async def stream_greeting_response(self, response_handler: ResponseHandler, prompt_type: str):
        """Stream greeting response with proper formatting"""
        # Show thinking message first
        await response_handler.emit_text_block(
            "STATUS", "Thinking about your query..."
        )
        
        response = self.get_greeting_response(prompt_type)
        
        # Create text stream for the greeting response
        greeting_stream = response_handler.create_text_stream("GREETING_RESPONSE")
        
        # Stream the response character by character for a nice effect
        for char in response:
            await greeting_stream.emit_chunk(char)
            # Small delay to make the streaming visible
            await asyncio.sleep(0.01)
        
        # Mark the text stream as complete
        await greeting_stream.complete()
    
    async def get_youtube_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get YouTube transcript with timestamps using Webshare proxy"""
        try:
            # Run the synchronous transcript extraction in a thread pool to avoid blocking
            def _extract_transcript():
                # Configure YouTube Transcript API with Webshare proxy
                ytt_api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username="bckefkmt-rotate",
                        proxy_password="klne0rjlnila",
                    )
                )
                
                # Get transcript list first, then fetch transcript
                transcript_list = ytt_api.list(video_id)
                transcript = transcript_list.find_transcript(['en'])
                fetched_transcript = transcript.fetch()
                
                # Convert to raw data for processing
                return fetched_transcript.to_raw_data() if hasattr(fetched_transcript, 'to_raw_data') else list(fetched_transcript)
            
            # Run the blocking operation in a thread pool with timeout
            transcript_data = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _extract_transcript),
                timeout=30.0  # 30 second timeout
            )
            
            # Format transcript with timestamps
            formatted_transcript = ""
            for entry in transcript_data:
                start_time = int(entry['start'])
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                formatted_transcript += f"{timestamp} {entry['text']}\n"
            
            # Also get plain text version
            plain_text = " ".join([entry['text'] for entry in transcript_data])
            
            return {
                "success": True,
                "transcript_with_timestamps": formatted_transcript,
                "plain_text": plain_text,
                "transcript_data": transcript_data
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "transcript_with_timestamps": "",
                "plain_text": "",
                "transcript_data": []
            }
    
    async def summarize_with_fireworks_stream(self, transcript: str, transcript_data: List[Dict]) -> AsyncIterator[str]:
        """Summarize transcript using Fireworks API with streaming"""
        
        # Create the prompt for summarization
        prompt = f"""You are a professional video content analyst. Analyze this YouTube video transcript and provide a comprehensive, detailed summary following this EXACT structure:

## General Summary
Write a detailed 3-4 paragraph overview covering:
- The main topic/subject of the video
- Key arguments, findings, or points discussed
- The creator's perspective or stance
- Overall conclusions or takeaways
- Target audience and purpose

## Section Breakdown
Create detailed subsections with descriptive headings based on the content flow. For each section:
- Use clear, descriptive subheading names (not generic terms like "Introduction")
- Include timestamp ranges in format [MM:SS] - [MM:SS] for each section
- Provide 2-3 sentences summarizing what happens in that time range
- Include specific details, examples, or data mentioned
- Quote important statements with their timestamps

RULES YOU MUST FOLLOW:
1. Be comprehensive - don't skip important details
2. Use the EXACT timestamp format: [MM:SS] - [MM:SS] for ranges, [MM:SS] for specific moments
3. Create 4-8 subsections depending on video length and content
4. Each subsection should be substantial (2-4 sentences minimum)
5. Include direct quotes when the speaker makes important points
6. Maintain chronological order based on timestamps
7. Use descriptive subheading names that reflect the actual content

Here is the transcript with timestamps:

{transcript}

Remember: This summary will be read by someone who hasn't watched the video. Make it detailed enough that they understand the full content and context."""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.3,
            "top_p": 0.9,
            "stream": True  # Enable streaming
        }
        
        headers = {
            "Authorization": f"Bearer {self.fireworks_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.fireworks_base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data == "[DONE]":
                                break
                            try:
                                import json
                                chunk_data = json.loads(data)
                                if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            yield f"Error generating summary: {str(e)}"
    
    async def assist(self, session: Session, query: Query, response_handler: ResponseHandler):
        """Main processing method for the agent"""
        
        # Extract YouTube URL from request
        youtube_url = self.find_youtube_url(query.prompt)
        lower_prompt = query.prompt.lower().strip()
        
        # Handle specific identity questions
        if lower_prompt in ['who are you', 'what do you do', 'what are you', 'who are you?', 'what do you do?', 'what are you?']:
            await self.stream_greeting_response(response_handler, "identity")
            await response_handler.complete()
            return
        
        # Handle general greetings
        elif lower_prompt in ['hi', 'hello', 'hey', 'hi!', 'hello!', 'hey!']:
            await self.stream_greeting_response(response_handler, "greeting")
            await response_handler.complete()
            return
        
        # Handle cases where no YouTube URL is provided
        elif not youtube_url:
            await self.stream_greeting_response(response_handler, "general")
            await response_handler.complete()
            return
        
        # If we get here, they provided a YouTube URL, so continue with normal processing
        
        # Extract video ID
        video_id = self.extract_youtube_video_id(youtube_url)
        if not video_id:
            # Show thinking message first
            await response_handler.emit_text_block(
                "STATUS", "Thinking about your query..."
            )
            
            # Create text stream for error response to prevent timeout
            error_stream = response_handler.create_text_stream("ERROR_RESPONSE")
            
            error_msg = """❌ **Invalid YouTube URL**

**This could be due to:**
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

            # Stream the error message
            for char in error_msg:
                await error_stream.emit_chunk(char)
                await asyncio.sleep(0.005)
            
            await error_stream.complete()
            await response_handler.complete()
            return
        
        # Send progress update - using text_block as per framework
        await response_handler.emit_text_block(
            "STATUS", f"Thinking about your query..."
        )
        
        # Get transcript
        transcript_result = await self.get_youtube_transcript(video_id)
        
        if not transcript_result["success"]:
            # Create text stream for error response to prevent timeout
            error_stream = response_handler.create_text_stream("ERROR_RESPONSE")
            
            # Clean up the error message from YouTube transcript API
            raw_error = str(transcript_result['error'])
            
            # Extract key information and create a cleaner error message
            if "No transcripts were found for any of the requested language codes: ['en']" in raw_error:
                clean_error = "No English captions available for this video"
            elif "This video is unavailable" in raw_error:
                clean_error = "Video is unavailable or private"
            elif "Subtitles are disabled" in raw_error:
                clean_error = "Captions are disabled for this video"
            elif "timeout" in raw_error.lower():
                clean_error = "Connection timeout while fetching transcript"
            else:
                # For other errors, take just the first meaningful line
                lines = raw_error.split('\n')
                clean_error = lines[0] if lines else raw_error[:100] + "..." if len(raw_error) > 100 else raw_error
            
            error_msg = f""" **Failed to extract transcript from video**


**This could be due to:**
- Video doesn't have English captions/subtitles
- Video is private or restricted  
- Captions are disabled

**Please try:**
- A different video with English captions
- Ensuring the video is publicly accessible
- Waiting a moment and trying again"""

            # Stream the error message
            for char in error_msg:
                await error_stream.emit_chunk(char)
                await asyncio.sleep(0.005)
            
            await error_stream.complete()
            await response_handler.complete()
            return
        
        
        # Send progress update
        await response_handler.emit_text_block(
            "STATUS", "Transcript extracted successfully. Generating summary..."
        )
        
        # Create text stream for the final response (following framework pattern)
        final_response_stream = response_handler.create_text_stream("FINAL_RESPONSE")
        
        # Stream the summary header
        await final_response_stream.emit_chunk("# YouTube Video Summary\n\n")
        
        # Stream the AI-generated summary
        try:
            async for chunk in self.summarize_with_fireworks_stream(
                transcript_result["transcript_with_timestamps"],
                transcript_result["transcript_data"]
            ):
                await final_response_stream.emit_chunk(chunk)
        except Exception as e:
            await final_response_stream.emit_chunk(f"\n\nError: {str(e)}")
        
        # Stream the footer
        await final_response_stream.emit_chunk(f"\n\n---\n*Summarized from: {youtube_url}*")
        
        # Mark the text stream as complete (required by framework)
        await final_response_stream.complete()
        
        # Mark the response as complete (required by framework)
        await response_handler.complete()


def main():
    """Main function to run the YouTube Summarizer Agent"""
    
    # Verify environment variables
    if not os.getenv("FIREWORKS_API_KEY"):
        print("Error: FIREWORKS_API_KEY environment variable is required")
        print("Set it with: export FIREWORKS_API_KEY='your-api-key-here'")
        return
    
    # Create and run the agent (following framework pattern)
    agent = YouTubeSummarizerAgent()
    server = DefaultServer(agent)
    
    print("🚀 Starting YouTube Summarizer Agent...")
    print("📝 Supports English captions only")
    print("🔥 Using Fireworks AI for summarization")
    print(f"🤖 Model: {agent.model}")
    print("🎯 Ready to process YouTube URLs!")
    print("📡 Server running with streaming support...")
    
    # Start the server (default port 8000) - framework handles SSE automatically
    server.run()


if __name__ == "__main__":
    main()