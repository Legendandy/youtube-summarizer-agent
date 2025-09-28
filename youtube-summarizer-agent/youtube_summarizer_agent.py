import os
import re
import asyncio
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
    
    async def get_youtube_transcript(self, video_id: str) -> Dict[str, Any]:
        """Get YouTube transcript with timestamps using Webshare proxy"""
        try:
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
            transcript_data = fetched_transcript.to_raw_data() if hasattr(fetched_transcript, 'to_raw_data') else list(fetched_transcript)
            
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
        prompt = f"""Please analyze this YouTube video transcript and provide a comprehensive summary with the following structure:

## General Summary
Provide a 2-3 paragraph overview of the video's main content and key points.

## Section Breakdown
Create subheadings for major topics/sections and include relevant timestamps from the transcript. Use the timestamp format [MM:SS] when referencing specific parts.

Here is the transcript with timestamps:

{transcript}

Please ensure your response includes:
1. A clear general summary
2. Organized subheadings for different topics
3. Specific timestamps for key sections
4. Important quotes or key points with their timestamps"""

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
        
        if not youtube_url:
            await response_handler.emit_error(
                "INPUT_ERROR", {"message": "Please provide a valid YouTube URL to summarize."}
            )
            await response_handler.complete()
            return
        
        # Extract video ID
        video_id = self.extract_youtube_video_id(youtube_url)
        if not video_id:
            await response_handler.emit_error(
                "URL_ERROR", {"message": "Could not extract video ID from the provided URL."}
            )
            await response_handler.complete()
            return
        
        # Send progress update - using text_block as per framework
        await response_handler.emit_text_block(
            "STATUS", f"🎥 Extracting transcript from video: {video_id}"
        )
        
        # Get transcript
        transcript_result = await self.get_youtube_transcript(video_id)
        
        if not transcript_result["success"]:
            error_msg = (f"Failed to get transcript: {transcript_result['error']}. This could be due to:\n"
                        f"- Video doesn't have English captions\n"
                        f"- Video is private or restricted\n"
                        f"- Captions are disabled\n"
                        f"- IP rate limiting (proxy may be needed)")
            await response_handler.emit_error("TRANSCRIPT_ERROR", {"message": error_msg})
            await response_handler.complete()
            return
        
        
        # Send progress update
        await response_handler.emit_text_block(
            "STATUS", "📝 Transcript extracted successfully. Generating summary..."
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