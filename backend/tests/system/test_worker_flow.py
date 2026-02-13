import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.processing_queue_service import processing_worker
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_full_worker_flow(mock_db, mock_gemini_service):
    # 1. Setup - Create a "pending" video and job
    video_id = "sys_test_video"
    video_doc = {
        "id": video_id,
        "course_id": "course_1",
        "title": "System Test Video",
        "description": "A video for system testing",
        "url": "gs://test/video.mp4",
        "duration": 60,
        "difficulty": "Medium",
        "topics": [],
        "order": 1,
        "processing_status": "pending"
    }
    await mock_db.videos.insert_one(video_doc)
    
    # Needs to match ProcessingJobDB
    job_doc = {
        "video_id": video_id,
        "status": "pending",
        "priority": 1,
        "retry_count": 0,
        "error_message": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await mock_db.processing_queue.insert_one(job_doc)
    
    # 2. Mock services
    mock_gemini_service.generate_topics.return_value = ["Test", "System"]
    mock_gemini_service.generate_transcript_summary.return_value = "Cleaned summary"
    
    with patch('app.services.processing_queue_service.transcript_service.get_transcript_with_rate_limit', new_callable=AsyncMock) as mock_trans:
        mock_trans.return_value = "This is a test transcript."
        
        with patch('app.services.processing_queue_service.embedding_module.embedding_service') as mock_emb_service:
            mock_emb_service.chunk_text.return_value = ["Chunk 1"]
            mock_emb_service.generate_embeddings_batch = AsyncMock(return_value=[[0.1]*384, [0.2]*384])
            mock_emb_service.MODEL_NAME = "test-model"
            
            # Mock enqueue_quiz_job to avoid Redis call
            with patch('app.services.processing_queue_service.enqueue_quiz_job', new_callable=AsyncMock):
                
                # 3. Execute - Run the worker function for this specific job
                job = await mock_db.processing_queue.find_one({"video_id": video_id})
                await processing_worker._process_single_job(job)
            
    # 4. Verify - Check if DB reflects completed status
    updated_video = await mock_db.videos.find_one({"id": video_id})
    assert updated_video["processing_status"] == "completed"
    assert updated_video["transcript"] == "This is a test transcript."
    
    updated_job = await mock_db.processing_queue.find_one({"video_id": video_id})
    assert updated_job["status"] == "completed"
