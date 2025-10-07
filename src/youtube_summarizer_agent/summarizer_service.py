import json
import httpx
from typing import List, Dict, AsyncIterator
from config.fireworks_config import FireworksConfig


class SummarizerService:
    """Generates AI summaries of video transcripts"""
    
    def __init__(self):
        """Initialize summarizer with Fireworks configuration"""
        self.config = FireworksConfig()
        self.config.validate()
    
    def _build_prompt(self, transcript: str) -> str:
        """
        Builds the prompt for AI summarization
        
        Args:
            transcript: Formatted transcript with timestamps
            
        Returns:
            Complete prompt string
        """
        return f"""You are a professional video content analyst. You will analyze the following YouTube transcript and produce a detailed structured summary.
You MUST follow the EXACT template and formatting rules below. No deviations are allowed.
        
        

YouTube Video Summary

General Summary

Write a detailed 2-3 paragraph overview of the video.

Focus strictly on what the creator says, demonstrates, or shows in the video.

Include the following points without interpreting, editorializing, or giving "takeaways":

The main topic or subject of the video.

Key items, products, or concepts presented.

Important demonstrations, comparisons, or examples shown.

The creator's perspective, style, or tone (e.g., conversational, enthusiastic).

Any notable features, measurements, or details emphasized in the video.

Avoid phrases like "overall conclusions," "takeaways," or "key arguments."

Present the summary in factual, descriptive language, as if reporting exactly what happens in the video.

Keep the audience in mind only insofar as the creator mentions them or it is obvious from the content.

The goal is a faithful, comprehensive overview of the video content, not an analysis or recommendation.

Section Breakdown

Create 4–8 subsections based on the flow of the transcript. For each section:

Use a descriptive subheading (never generic names like "Introduction," "Conclusion," or "Summary")

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

No filler commentary like "This section highlights" — just describe what was said.

Here is the transcript with timestamps:

{transcript}"""
    
    async def summarize_stream(self, transcript: str, transcript_data: List[Dict]) -> AsyncIterator[str]:
        """
        Generates streaming summary of transcript
        
        Args:
            transcript: Formatted transcript with timestamps
            transcript_data: Raw transcript data (for future use)
            
        Yields:
            Chunks of generated summary text
        """
        prompt = self._build_prompt(transcript)
        
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        payload = self.config.get_payload(messages)
        headers = self.config.get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=self.config.TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    self.config.BASE_URL,
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
                                chunk_data = json.loads(data)
                                if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            yield f"Error generating summary: {str(e)}"