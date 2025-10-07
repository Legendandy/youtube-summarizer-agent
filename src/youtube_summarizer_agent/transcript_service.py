import asyncio
from typing import Dict, Any, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from config.youtube_config import YouTubeConfig


class TranscriptService:
    """Extracts transcripts from YouTube videos"""
    
    def __init__(self):
        """Initialize transcript service with configuration"""
        self.config = YouTubeConfig()
    
    async def get_youtube_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        Fetches transcript for a YouTube video
        
        Args:
            video_id: YouTube video ID (11 characters)
            
        Returns:
            Dict containing:
                - success: bool
                - transcript_with_timestamps: formatted transcript with [MM:SS] timestamps
                - plain_text: transcript without timestamps
                - transcript_data: raw transcript data
                - error: error message if failed
        """
        try:
            def _extract_transcript():
                """Internal function to extract transcript (runs in executor)"""
                ytt_api = YouTubeTranscriptApi(
                    proxy_config=WebshareProxyConfig(
                        proxy_username=self.config.PROXY_USERNAME,
                        proxy_password=self.config.PROXY_PASSWORD,
                    )
                )
                
                transcript_list = ytt_api.list(video_id)
                transcript = transcript_list.find_transcript([self.config.DEFAULT_LANGUAGE])
                fetched_transcript = transcript.fetch()
                
                return fetched_transcript.to_raw_data() if hasattr(fetched_transcript, 'to_raw_data') else list(fetched_transcript)
            
            # Run transcript extraction with timeout
            transcript_data = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _extract_transcript),
                timeout=self.config.TRANSCRIPT_TIMEOUT
            )
            
            # Format transcript with timestamps
            formatted_transcript = self._format_with_timestamps(transcript_data)
            
            # Create plain text version
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
    
    def _format_with_timestamps(self, transcript_data: List[Dict]) -> str:
        """
        Formats transcript with [MM:SS] timestamps
        
        Args:
            transcript_data: Raw transcript data from YouTube API
            
        Returns:
            Formatted transcript string
        """
        formatted_transcript = ""
        for entry in transcript_data:
            start_time = int(entry['start'])
            minutes = start_time // 60
            seconds = start_time % 60
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            formatted_transcript += f"{timestamp} {entry['text']}\n"
        
        return formatted_transcript
    
    def parse_error(self, error: str) -> str:
        """
        Parses raw error message into user-friendly format
        
        Args:
            error: Raw error message
            
        Returns:
            Clean, user-friendly error message
        """
        raw_error = str(error)
        
        if "No transcripts were found for any of the requested language codes: ['en']" in raw_error:
            return "No English captions available for this video"
        elif "This video is unavailable" in raw_error:
            return "Video is unavailable or private"
        elif "Subtitles are disabled" in raw_error:
            return "Captions are disabled for this video"
        elif "timeout" in raw_error.lower():
            return "Connection timeout while fetching transcript"
        else:
            # Return first line of error or truncated version
            lines = raw_error.split('\n')
            clean_error = lines[0] if lines else raw_error[:100] + "..." if len(raw_error) > 100 else raw_error
            return clean_error