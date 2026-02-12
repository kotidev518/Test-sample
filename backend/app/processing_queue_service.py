"""
Processing Queue Service - Background worker for async video processing
Handles transcript fetching and embedding generation with:
  - Max 3 concurrent requests (asyncio.Semaphore) to prevent IP bans
  - 2-5s random delay between transcript requests
  - Exponential backoff with jitter on failures
  - Per-video processing status tracking in MongoDB
"""
import asyncio
import random
from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId

from .database import db
from .transcript_service import transcript_service
from . import embedding_service as embedding_module
from .queue import enqueue_quiz_job


class ProcessingQueueWorker:
    """Background worker that processes videos concurrently with rate limiting"""

    def __init__(self, max_concurrent: int = 3):
        self.is_running = False
        self.poll_interval = 5  # Check queue every 5 seconds
        self.rate_limit_delay = (2, 5)  # 2-5 seconds between transcript requests
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.max_retries = 3

    async def start_worker(self):
        """
        Start the background worker loop.
        Processes up to max_concurrent jobs in parallel every poll_interval seconds.
        """
        self.is_running = True
        print(f"🚀 Processing queue worker started (max_concurrent={self.max_concurrent})")

        try:
            while self.is_running:
                try:
                    await self._process_batch()
                except Exception as e:
                    print(f"Worker batch error: {e}")

                await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            print("⏹️  Processing queue worker stopped")
            self.is_running = False
            raise

    async def stop_worker(self):
        """Stop the background worker"""
        self.is_running = False
        print("Stopping processing queue worker...")

    # ------------------------------------------------------------------ #
    #  Core concurrent processing
    # ------------------------------------------------------------------ #

    async def _process_batch(self):
        """
        Claim up to max_concurrent pending jobs and process them concurrently.
        Each job is gated by the semaphore to enforce the concurrency limit.
        """
        jobs = await self._claim_pending_jobs(self.max_concurrent)
        if not jobs:
            return

        print(f"📦 Processing batch of {len(jobs)} jobs concurrently")
        tasks = [
            asyncio.create_task(self._process_with_semaphore(job))
            for job in jobs
        ]
        # Wait for all tasks; exceptions are captured per-task
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _claim_pending_jobs(self, limit: int) -> List[dict]:
        """
        Atomically claim up to `limit` pending jobs by setting their status
        to 'processing'. Uses find_one_and_update in a loop to avoid races.
        """
        claimed = []
        for _ in range(limit):
            job = await db.processing_queue.find_one_and_update(
                {"status": "pending"},
                {
                    "$set": {
                        "status": "processing",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                sort=[("priority", -1), ("created_at", 1)],
                return_document=True,
            )
            if not job:
                break
            claimed.append(job)
        return claimed

    async def _process_with_semaphore(self, job: dict):
        """Gate a single job through the semaphore, then process it."""
        async with self._semaphore:
            await self._process_single_job(job)

    async def _process_single_job(self, job: dict):
        """
        Process one video job:
          1. Fetch transcript (with 2-5s random delay + exponential backoff)
          2. Generate SBERT embedding
          3. Store both in the videos collection
          4. Update queue job status
        """
        video_id = job["video_id"]
        print(f"📹 Processing video: {video_id}")

        try:
            # Step 1: Fetch video from database
            video = await db.videos.find_one({"id": video_id})
            if not video:
                raise Exception(f"Video {video_id} not found in database")

            # Step 2: Fetch transcript with rate limiting (2-5s random delay)
            print(f"  📝 Fetching transcript for {video_id}...")
            youtube_video_id = video.get("id", video_id)

            transcript = await transcript_service.get_transcript_with_rate_limit(
                youtube_video_id,
                delay_range=self.rate_limit_delay,
            )

            if not transcript:
                raise Exception(f"Failed to fetch transcript for {youtube_video_id}")

            print(f"  ✓ Transcript fetched ({len(transcript)} chars)")

            # Step 3: Generate SBERT embedding
            print(f"  🧠 Generating embedding for {video_id}...")
            embedding_binary = await embedding_module.embedding_service.generate_embedding(transcript)

            if not embedding_binary:
                raise Exception("Failed to generate embedding")

            print(f"  ✓ Embedding generated")

            # Step 4: Enqueue Quiz Generation to ARQ
            # This offloads the slow AI work to a robust queue with parallelism and retries
            await enqueue_quiz_job(video_id)

            # Step 5: Update video with transcript and embedding
            now = datetime.now(timezone.utc)
            update_result = await db.videos.update_one(
                {"id": video_id},
                {
                    "$set": {
                        "transcript": transcript,
                        "embedding": embedding_binary,
                        "embedding_model": embedding_module.embedding_service.MODEL_NAME,
                        "processing_status": "completed",
                        "embedding_generated_at": now,
                        "transcript_fetched_at": now,
                    }
                },
            )

            if update_result.modified_count == 0:
                print(f"  ⚠️ Warning: Video {video_id} not updated")

            # Step 5: Mark job as completed
            await db.processing_queue.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": "completed",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            print(f"  ✅ Video {video_id} processed successfully")

        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Error processing {video_id}: {error_msg}")
            await self._handle_job_failure(job, error_msg)

    # ------------------------------------------------------------------ #
    #  Failure handling with exponential backoff
    # ------------------------------------------------------------------ #

    async def _handle_job_failure(self, job: dict, error_msg: str):
        """
        Handle a failed job:
          - Increment retry count
          - If retries exhausted → mark as 'failed'
          - Otherwise → apply exponential backoff delay, then reset to 'pending'
        """
        video_id = job["video_id"]
        retry_count = job.get("retry_count", 0) + 1

        if retry_count >= self.max_retries:
            # Mark as permanently failed
            await db.processing_queue.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error_msg,
                        "retry_count": retry_count,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            await db.videos.update_one(
                {"id": video_id},
                {"$set": {"processing_status": "failed"}},
            )
            print(f"  ⛔ Video {video_id} failed after {retry_count} retries")
        else:
            # Exponential backoff: 2^retry seconds with ±20% jitter
            backoff = (2 ** retry_count)
            jitter = backoff * random.uniform(-0.2, 0.2)
            wait_time = backoff + jitter

            print(
                f"  🔄 Retry {retry_count}/{self.max_retries} for {video_id} "
                f"(backoff {wait_time:.1f}s)"
            )
            await asyncio.sleep(wait_time)

            # Reset to pending for the next batch cycle to pick up
            await db.processing_queue.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": "pending",
                        "error_message": error_msg,
                        "retry_count": retry_count,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

    # ------------------------------------------------------------------ #
    #  Queue management helpers
    # ------------------------------------------------------------------ #

    async def add_to_queue(self, video_id: str, priority: int = 0) -> bool:
        """
        Add a video to the processing queue.

        Args:
            video_id: Video ID to process
            priority: Priority (higher = processed first)

        Returns:
            True if added successfully, False if already in queue
        """
        try:
            existing = await db.processing_queue.find_one({"video_id": video_id})
            if existing:
                print(f"Video {video_id} already in queue (status: {existing.get('status')})")
                return False

            job = {
                "video_id": video_id,
                "status": "pending",
                "priority": priority,
                "retry_count": 0,
                "error_message": "",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            await db.processing_queue.insert_one(job)
            print(f"✓ Added {video_id} to processing queue (priority: {priority})")
            return True

        except Exception as e:
            print(f"Error adding {video_id} to queue: {e}")
            return False

    async def add_batch_to_queue(
        self, video_ids: List[str], priority: int = 0
    ) -> dict:
        """
        Add multiple videos to the queue.

        Args:
            video_ids: List of video IDs
            priority: Priority for all videos

        Returns:
            Dict with success/failure counts
        """
        results = {"queued": 0, "skipped": 0, "failed": 0}

        for video_id in video_ids:
            success = await self.add_to_queue(video_id, priority)
            if success:
                results["queued"] += 1
            else:
                results["skipped"] += 1

        return results

    async def get_queue_status(self) -> dict:
        """
        Get current queue statistics.

        Returns:
            Dict with counts by status
        """
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]

        results = await db.processing_queue.aggregate(pipeline).to_list(length=10)

        status = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}

        for item in results:
            status[item["_id"]] = item["count"]

        return status

    async def get_course_processing_status(self, course_id: str) -> dict:
        """
        Get processing status for all videos in a specific course.

        Args:
            course_id: The course ID to check

        Returns:
            Dict with total, counts by status, and failed video details
        """
        # Aggregate processing_status from the videos collection
        pipeline = [
            {"$match": {"course_id": course_id}},
            {
                "$group": {
                    "_id": "$processing_status",
                    "count": {"$sum": 1},
                }
            },
        ]

        results = await db.videos.aggregate(pipeline).to_list(length=10)

        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        total = 0
        for item in results:
            key = item["_id"] or "pending"
            status_counts[key] = item["count"]
            total += item["count"]

        # Fetch failed videos with error info from the queue
        failed_videos = []
        if status_counts["failed"] > 0:
            failed_cursor = db.processing_queue.find(
                {"status": "failed"},
                {"video_id": 1, "error_message": 1, "retry_count": 1, "_id": 0},
            )
            async for doc in failed_cursor:
                # Only include if video belongs to this course
                video = await db.videos.find_one(
                    {"id": doc["video_id"], "course_id": course_id},
                    {"_id": 0, "id": 1},
                )
                if video:
                    failed_videos.append(
                        {
                            "video_id": doc["video_id"],
                            "error": doc.get("error_message", ""),
                            "retries": doc.get("retry_count", 0),
                        }
                    )

        return {
            "course_id": course_id,
            "total_videos": total,
            **status_counts,
            "failed_videos": failed_videos,
        }

    async def retry_failed_jobs(self) -> int:
        """
        Retry all failed jobs (reset to pending).

        Returns:
            Number of jobs reset
        """
        result = await db.processing_queue.update_many(
            {"status": "failed"},
            {
                "$set": {
                    "status": "pending",
                    "retry_count": 0,
                    "error_message": "",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        count = result.modified_count
        print(f"🔄 Reset {count} failed jobs to pending")
        return count

    async def clear_completed_jobs(self, older_than_days: int = 7) -> int:
        """
        Remove completed jobs older than specified days.

        Args:
            older_than_days: Remove jobs older than this many days

        Returns:
            Number of jobs removed
        """
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        result = await db.processing_queue.delete_many(
            {"status": "completed", "updated_at": {"$lt": cutoff_date}}
        )

        count = result.deleted_count
        print(f"🗑️  Removed {count} completed jobs older than {older_than_days} days")
        return count


# Singleton instance
processing_worker = ProcessingQueueWorker(max_concurrent=3)
