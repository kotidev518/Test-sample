"""
YouTube Data API Service for fetching playlist and video metadata
"""
import re
import aiohttp
from typing import Optional, List, Dict, Any
from .config import settings


class YouTubeService:
    """Service to interact with YouTube Data API v3"""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """Extract playlist ID from various YouTube URL formats"""
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',  # Standard playlist URL
            r'playlist\?list=([a-zA-Z0-9_-]+)',  # playlist URL
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_playlist_details(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Fetch playlist metadata (title, description, thumbnail)"""
        params = {
            'part': 'snippet',
            'id': playlist_id,
            'key': self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/playlists", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"YouTube API error: {error_text}")
                    return None
                    
                data = await response.json()
                items = data.get('items', [])
                
                if not items:
                    return None
                
                snippet = items[0]['snippet']
                thumbnails = snippet.get('thumbnails', {})
                
                # Get best quality thumbnail
                thumbnail_url = ''
                for quality in ['maxres', 'high', 'medium', 'default']:
                    if quality in thumbnails:
                        thumbnail_url = thumbnails[quality].get('url', '')
                        break
                
                return {
                    'id': playlist_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'thumbnail': thumbnail_url,
                    'channel_title': snippet.get('channelTitle', '')
                }
    
    async def get_playlist_videos(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Fetch all videos from a playlist with pagination"""
        videos = []
        page_token = None
        
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': playlist_id,
                    'maxResults': 50,  # Max allowed by YouTube API
                    'key': self.api_key
                }
                
                if page_token:
                    params['pageToken'] = page_token
                
                async with session.get(f"{self.BASE_URL}/playlistItems", params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"YouTube API error fetching videos: {error_text}")
                        break
                    
                    data = await response.json()
                    items = data.get('items', [])
                    
                    for i, item in enumerate(items):
                        snippet = item['snippet']
                        content_details = item.get('contentDetails', {})
                        thumbnails = snippet.get('thumbnails', {})
                        
                        # Get best quality thumbnail
                        thumbnail_url = ''
                        for quality in ['maxres', 'high', 'medium', 'default']:
                            if quality in thumbnails:
                                thumbnail_url = thumbnails[quality].get('url', '')
                                break
                        
                        video_id = content_details.get('videoId', snippet.get('resourceId', {}).get('videoId', ''))
                        
                        if video_id:  # Skip deleted/private videos
                            videos.append({
                                'video_id': video_id,
                                'title': snippet.get('title', ''),
                                'description': snippet.get('description', ''),
                                'thumbnail': thumbnail_url,
                                'position': snippet.get('position', len(videos)),
                                'published_at': snippet.get('publishedAt', '')
                            })
                    
                    # Check for next page
                    page_token = data.get('nextPageToken')
                    if not page_token:
                        break
        
        return videos
    
    async def get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch detailed info for videos (duration, tags, etc.)"""
        if not video_ids:
            return {}
        
        details = {}
        
        async with aiohttp.ClientSession() as session:
            # YouTube API allows max 50 video IDs per request
            for i in range(0, len(video_ids), 50):
                batch = video_ids[i:i+50]
                params = {
                    'part': 'snippet,contentDetails',
                    'id': ','.join(batch),
                    'key': self.api_key
                }
                
                async with session.get(f"{self.BASE_URL}/videos", params=params) as response:
                    if response.status != 200:
                        continue
                    
                    data = await response.json()
                    
                    for item in data.get('items', []):
                        vid = item['id']
                        snippet = item.get('snippet', {})
                        content_details = item.get('contentDetails', {})
                        
                        # Parse duration (ISO 8601 format: PT4M13S)
                        duration_str = content_details.get('duration', 'PT0S')
                        duration_seconds = self._parse_duration(duration_str)
                        
                        # Extract tags as topics
                        tags = snippet.get('tags', [])[:5]  # Limit to 5 tags
                        if not tags:
                            # Fallback: extract keywords from title
                            tags = self._extract_keywords(snippet.get('title', ''))
                        
                        details[vid] = {
                            'duration': duration_seconds,
                            'tags': tags,
                            'category_id': snippet.get('categoryId', '')
                        }
        
        return details
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract simple keywords from title as fallback topics"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are', 'was', 'were', 'how', 'what', 'why', 'when', 'where', 'who'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        keywords = [w.capitalize() for w in words if w not in stop_words]
        return keywords[:3]  # Return top 3 keywords


# Singleton instance
youtube_service = YouTubeService()
