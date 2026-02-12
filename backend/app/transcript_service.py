"""
YouTube Transcript Service — fetches real video transcripts
using youtube-transcript-api to replace description-based content.
Includes rate limiting and exponential backoff to prevent IP bans.
"""
import asyncio
import random
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


class TranscriptService:
    """Service to fetch YouTube video transcripts"""

    MAX_TRANSCRIPT_CHARS = 5000  # Cap to keep Gemini prompts reasonable

    def __init__(self):
        self._api = YouTubeTranscriptApi()

    def _fetch_transcript_sync(self, video_id: str) -> Optional[str]:
        """
        Synchronously fetch a transcript for a single video.
        Tries English first, then falls back to any available language.
        Returns the joined transcript text or None on failure.
        """
        try:
            # Try fetching English transcript directly
            transcript = self._api.fetch(video_id, languages=["en"])
            return self._join_entries(transcript)
        except NoTranscriptFound:
            pass
        except (TranscriptsDisabled, VideoUnavailable) as e:
            print(f"Transcript unavailable for {video_id}: {e}")
            return None
        except Exception as e:
            print(f"Transcript error (en) for {video_id}: {e}")

        # Fallback: try listing all available transcripts and pick the first one
        try:
            transcript_list = self._api.list(video_id)
            for t in transcript_list:
                try:
                    # Try to translate to English
                    translated = t.translate("en")
                    fetched = translated.fetch()
                    return self._join_entries(fetched)
                except Exception:
                    # If translation fails, use original
                    try:
                        fetched = t.fetch()
                        return self._join_entries(fetched)
                    except Exception:
                        continue
        except (TranscriptsDisabled, VideoUnavailable) as e:
            print(f"Transcript unavailable for {video_id}: {e}")
        except Exception as e:
            print(f"Unexpected transcript error for {video_id}: {e}")

        return None

    def _join_entries(self, entries) -> str:
        """Join transcript entries into a single string, capped at MAX_TRANSCRIPT_CHARS"""
        text = " ".join(snippet.text for snippet in entries)
        return text[: self.MAX_TRANSCRIPT_CHARS]

    async def get_transcript(self, video_id: str) -> str:
        """
        Async wrapper — fetch transcript for a single video.
        Returns transcript text or empty string if unavailable.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._fetch_transcript_sync, video_id)
        return result or ""
    
    async def get_transcript_with_rate_limit(
        self,
        video_id: str,
        delay_range: tuple = (2, 5)
    ) -> str:
        """
        Fetch transcript with rate limiting to prevent IP bans.
        Adds random delay between min and max seconds.
        Implements exponential backoff with jitter on failures.
        
        Args:
            video_id: YouTube video ID
            delay_range: Tuple of (min_delay, max_delay) in seconds
        
        Returns:
            Transcript text or empty string if unavailable
        """
        # Add random delay before request (rate limiting)
        delay = random.uniform(delay_range[0], delay_range[1])
        await asyncio.sleep(delay)
        
        # Fetch with retry and exponential backoff
        result = await self._retry_with_backoff(video_id, max_retries=3)
        return result or ""
    
    async def _retry_with_backoff(
        self,
        video_id: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Retry transcript fetching with exponential backoff and jitter.
        
        Backoff schedule: 1s, 2s, 4s (with ±20% jitter)
        
        Args:
            video_id: YouTube video ID
            max_retries: Maximum number of retry attempts
        
        Returns:
            Transcript text or None on failure
        """
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._fetch_transcript_sync,
                    video_id
                )
                
                if result:
                    if attempt > 0:
                        print(f"✓ Transcript fetched for {video_id} on retry {attempt}")
                    return result
                
                # No transcript available (not an error, just unavailable)
                return None
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Calculate backoff: 2^attempt seconds with jitter
                    backoff = (2 ** attempt)
                    jitter = backoff * random.uniform(-0.2, 0.2)  # ±20% jitter
                    wait_time = backoff + jitter
                    
                    print(f"⚠️ Transcript fetch failed for {video_id} (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"   Retrying in {wait_time:.1f}s...")
                    
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Transcript fetch failed for {video_id} after {max_retries} attempts: {e}")
                    return None
        
        return None

    async def get_transcripts_batch(self, video_ids: List[str]) -> Dict[str, str]:
        """
        Fetch transcripts for multiple videos concurrently.
        Returns a dict mapping video_id → transcript_text.
        Videos without transcripts will have an empty string.
        """
        tasks = [self.get_transcript(vid) for vid in video_ids]
        results = await asyncio.gather(*tasks)
        return dict(zip(video_ids, results))


# Singleton instance
transcript_service = TranscriptService()
