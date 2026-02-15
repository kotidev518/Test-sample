import asyncio
from datetime import datetime, timezone
from typing import List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from app.services.youtube_service import youtube_service
from app.schemas import CourseDB, VideoDB
from app.services.processing_queue_service import processing_worker

class PlaylistService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def import_playlist(self, playlist_url: str, difficulty: str, admin_id: str) -> Tuple[bool, str, dict]:
        """
        Import a YouTube playlist as a course.
        Returns: (success, message, course_data)
        """
        playlist_id = youtube_service.extract_playlist_id(playlist_url)
        if not playlist_id:
            return False, "Invalid YouTube playlist URL.", {}
        
        # Check if playlist already imported
        existing_course = await self.db.courses.find_one({"id": playlist_id})
        if existing_course:
            return False, f"This playlist has already been imported as '{existing_course['title']}'", {}
        
        # Fetch playlist details
        playlist_details = await youtube_service.get_playlist_details(playlist_id)
        if not playlist_details:
            return False, "Could not fetch playlist details.", {}
        
        # Fetch all videos from playlist
        playlist_videos = await youtube_service.get_playlist_videos(playlist_id)
        if not playlist_videos:
            return False, "No videos found in this playlist.", {}
        
        # Get detailed info for all videos
        video_ids = [v['video_id'] for v in playlist_videos]
        video_details = await youtube_service.get_video_details(video_ids)
        
        # Extract topics
        all_tags = set()
        for vid in video_ids:
            details = video_details.get(vid, {})
            for tag in details.get('tags', []):
                all_tags.add(tag)
        course_topics = list(all_tags)[:10] if all_tags else ['General']
        
        # Decide which thumbnail to use for the course
        course_thumbnail = playlist_details['thumbnail']
        if "landscape" in course_thumbnail or not course_thumbnail:
            if playlist_videos:
                course_thumbnail = playlist_videos[0]['thumbnail']
        
        course_doc = CourseDB(
            id=playlist_id,
            title=playlist_details['title'],
            description=playlist_details['description'] or f"Course: {playlist_details['title']}",
            difficulty=difficulty,
            topics=course_topics,
            thumbnail=course_thumbnail,
            video_count=len(playlist_videos),
            channel=playlist_details['channel_title'],
            imported_at=datetime.now(timezone.utc).isoformat(),
            imported_by=admin_id
        )
        
        video_docs = []
        total_videos = len(playlist_videos)
        
        for video in playlist_videos:
            vid = video['video_id']
            details = video_details.get(vid, {})
            position = video['position']
            video_difficulty = self._get_progressive_difficulty(position, total_videos)
            
            video_tags = details.get('tags', [])[:5]
            if not video_tags:
                video_tags = course_topics[:3]
            
            video_docs.append(VideoDB(
                id=vid,
                course_id=playlist_id,
                title=video['title'],
                description=video['description'] or f"Part of {playlist_details['title']}",
                url=f"https://www.youtube.com/watch?v={vid}",
                duration=details.get('duration', 0),
                difficulty=video_difficulty,
                topics=video_tags,
                transcript="",
                order=position,
                thumbnail=video['thumbnail'],
                processing_status="pending"
            ))
        
        try:
            await self.db.courses.insert_one(course_doc.model_dump())
            if video_docs:
                await self.db.videos.insert_many([v.model_dump() for v in video_docs])
            
            # Queue for processing
            video_ids_to_queue = [v.id for v in video_docs]
            await processing_worker.add_batch_to_queue(video_ids_to_queue, priority=1)
            asyncio.create_task(processing_worker.start_worker())
            
            return True, "Imported successfully.", {
                "course_id": playlist_id,
                "course_title": playlist_details['title'],
                "videos_imported": len(video_docs)
            }
        except Exception as e:
            # Rollback
            await self.db.courses.delete_one({"id": playlist_id})
            await self.db.videos.delete_many({"course_id": playlist_id})
            return False, f"Database error: {str(e)}", {}

    def _get_progressive_difficulty(self, position: int, total_videos: int) -> str:
        if total_videos <= 1:
            return "Medium"
        progress = position / (total_videos - 1)
        if progress < 0.33: return "Easy"
        elif progress < 0.67: return "Medium"
        else: return "Hard"
