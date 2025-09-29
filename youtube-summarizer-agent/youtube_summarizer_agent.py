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

load_dotenv()


class YouTubeSummarizerAgent(AbstractAgent):
    def __init__(self):
        super().__init__("YouTube Summarizer")
        self.fireworks_api_key = os.getenv("FIREWORKS_API_KEY")
        if not self.fireworks_api_key:
            raise ValueError("FIREWORKS_API_KEY environment variable is required")
        
        self.fireworks_base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "x-ai/grok-4-fast:free"
    
    def extract_youtube_video_id(self, url: str) -> Optional[str]:
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
        await response_handler.emit_text_block(
            "STATUS", "Thinking about your query..."
        )
        
        response = self.get_greeting_response(prompt_type)
        
        greeting_stream = response_handler.create_text_stream("GREETING_RESPONSE")
        
        for char in response:
            await greeting_stream.emit_chunk(char)
            await asyncio.sleep(0.01)
        
        await greeting_stream.complete()
    
    async def get_youtube_transcript(self, video_id: str) -> Dict[str, Any]:
        try:
            def _extract_transcript():
                ytt_api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username="bckefkmt-rotate",
                        proxy_password="klne0rjlnila",
                    )
                )
                
                transcript_list = ytt_api.list(video_id)
                transcript = transcript_list.find_transcript(['en'])
                fetched_transcript = transcript.fetch()
                
                return fetched_transcript.to_raw_data() if hasattr(fetched_transcript, 'to_raw_data') else list(fetched_transcript)
            
            transcript_data = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _extract_transcript),
                timeout=30.0
            )
            
            formatted_transcript = ""
            for entry in transcript_data:
                start_time = int(entry['start'])
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                formatted_transcript += f"{timestamp} {entry['text']}\n"
            
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
        prompt = f"""You are a professional video content analyst. You will analyze the following YouTube transcript and produce a detailed structured summary.
You MUST follow the EXACT template and formatting rules below. No deviations are allowed.
        
        

YouTube Video Summary

General Summary

Write a detailed 2-3 paragraph overview of the video.

Focus strictly on what the creator says, demonstrates, or shows in the video.

Include the following points without interpreting, editorializing, or giving “takeaways”:

The main topic or subject of the video.

Key items, products, or concepts presented.

Important demonstrations, comparisons, or examples shown.

The creator’s perspective, style, or tone (e.g., conversational, enthusiastic).

Any notable features, measurements, or details emphasized in the video.

Avoid phrases like “overall conclusions,” “takeaways,” or “key arguments.”

Present the summary in factual, descriptive language, as if reporting exactly what happens in the video.

Keep the audience in mind only insofar as the creator mentions them or it is obvious from the content.

The goal is a faithful, comprehensive overview of the video content, not an analysis or recommendation.

Section Breakdown

Create 4–8 subsections based on the flow of the transcript. For each section:

Use a descriptive subheading (never generic names like “Introduction,” “Conclusion,” or “Summary”)

Add a timestamp range in the format: [MM:SS] - [MM:SS]

Write at least 4 sentences summarizing what was said only in that time range

Include specific details, examples, or comparisons mentioned

No interpretation, no commentary — just report what the speaker actually said

Maintain strict chronological order

CRITICAL RULES

Do not add, remove, or rename headings — only use General Summary and Section Breakdown.

Do not merge unrelated parts of the transcript — create a new subsection if the topic shifts.

Every subsection must be substantial (4+ sentences).

Every subsection must have a clear descriptive name that reflects the content.

Every timestamp range must be correct and formatted [MM:SS] - [MM:SS].

Do not shorten the general summary — always 4 full paragraphs.

No filler commentary like “This section highlights” — just describe what was said.

Here is the transcript with timestamps:

{transcript}"""

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
            "stream": True
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
                            data = line[6:]
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
        youtube_url = self.find_youtube_url(query.prompt)
        lower_prompt = query.prompt.lower().strip()
        
        if lower_prompt in ['who are you', 'what do you do', 'what are you', 'who are you?', 'what do you do?', 'what are you?']:
            await self.stream_greeting_response(response_handler, "identity")
            await response_handler.complete()
            return
        
        elif lower_prompt in ['hi', 'hello', 'hey', 'hi!', 'hello!', 'hey!']:
            await self.stream_greeting_response(response_handler, "greeting")
            await response_handler.complete()
            return
        
        elif not youtube_url:
            await self.stream_greeting_response(response_handler, "general")
            await response_handler.complete()
            return
        
        video_id = self.extract_youtube_video_id(youtube_url)
        if not video_id:
            await response_handler.emit_text_block(
                "STATUS", "Thinking about your query..."
            )
            
            error_stream = response_handler.create_text_stream("ERROR_RESPONSE")
            
            error_msg = """ **Invalid YouTube URL**

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

            for char in error_msg:
                await error_stream.emit_chunk(char)
                await asyncio.sleep(0.005)
            
            await error_stream.complete()
            await response_handler.complete()
            return
        
        await response_handler.emit_text_block(
            "STATUS", f"Thinking about your query..."
        )
        
        transcript_result = await self.get_youtube_transcript(video_id)
        
        if not transcript_result["success"]:
            error_stream = response_handler.create_text_stream("ERROR_RESPONSE")
            
            raw_error = str(transcript_result['error'])
            
            if "No transcripts were found for any of the requested language codes: ['en']" in raw_error:
                clean_error = "No English captions available for this video"
            elif "This video is unavailable" in raw_error:
                clean_error = "Video is unavailable or private"
            elif "Subtitles are disabled" in raw_error:
                clean_error = "Captions are disabled for this video"
            elif "timeout" in raw_error.lower():
                clean_error = "Connection timeout while fetching transcript"
            else:
                lines = raw_error.split('\n')
                clean_error = lines[0] if lines else raw_error[:100] + "..." if len(raw_error) > 100 else raw_error
            
            error_msg = f""" **Failed to extract transcript from video**


**This could be due to:**
- Video doesn't have English captions/subtitles
- Video is private or age restricted 
- Captions are disabled

**Please try:**
- A different video with English captions
- Ensuring the video is publicly accessible
- Waiting a moment and trying again"""

            for char in error_msg:
                await error_stream.emit_chunk(char)
                await asyncio.sleep(0.005)
            
            await error_stream.complete()
            await response_handler.complete()
            return
        
        await response_handler.emit_text_block(
            "STATUS", "Transcript extracted successfully. Generating summary..."
        )
        
        final_response_stream = response_handler.create_text_stream("FINAL_RESPONSE")
        
        await final_response_stream.emit_chunk("# YouTube Video Summary\n\n")
        
        try:
            async for chunk in self.summarize_with_fireworks_stream(
                transcript_result["transcript_with_timestamps"],
                transcript_result["transcript_data"]
            ):
                await final_response_stream.emit_chunk(chunk)
        except Exception as e:
            await final_response_stream.emit_chunk(f"\n\nError: {str(e)}")
        
        await final_response_stream.emit_chunk(f"\n\n---\n*Summarized from: {youtube_url}*")
        
        await final_response_stream.complete()
        
        await response_handler.complete()


def main():
    if not os.getenv("FIREWORKS_API_KEY"):
        print("Error: FIREWORKS_API_KEY environment variable is required")
        print("Set it with: export FIREWORKS_API_KEY='your-api-key-here'")
        return
    
    agent = YouTubeSummarizerAgent()
    server = DefaultServer(agent)
    
    print("🚀 Starting YouTube Summarizer Agent...")
    print("📝 Supports English captions only")
    print("🔥 Using Fireworks AI for summarization")
    print(f"🤖 Model: {agent.model}")
    print("🎯 Ready to process YouTube URLs!")
    print("📡 Server running with streaming support...")
    
    server.run()


if __name__ == "__main__":
    main()