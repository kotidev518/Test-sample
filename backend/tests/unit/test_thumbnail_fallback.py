
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.playlist_service import PlaylistService
from app.schemas import CourseDB

@pytest.mark.asyncio
async def test_import_playlist_thumbnail_fallback():
    # Mock DB
    mock_db = MagicMock()
    mock_db.courses.find_one = AsyncMock(return_value=None)
    mock_db.courses.insert_one = AsyncMock()
    mock_db.videos.insert_many = AsyncMock()
    
    # Mock YouTube Service
    with pytest.MonkeyPatch.context() as mp:
        mock_yt = MagicMock()
        mock_yt.extract_playlist_id.return_value = "test_playlist_id"
        mock_yt.get_playlist_details = AsyncMock(return_value={
            'title': 'Test Course',
            'description': 'Description',
            'thumbnail': 'https://i9.ytimg.com/landscape_maxresdefault.jpg', # Broken thumbnail
            'channel_title': 'Test Channel'
        })
        mock_yt.get_playlist_videos = AsyncMock(return_value=[
            {'video_id': 'vid1', 'title': 'Vid 1', 'description': '', 'thumbnail': 'https://working-thumb.jpg', 'position': 0}
        ])
        mock_yt.get_video_details = AsyncMock(return_value={
            'vid1': {'duration': 100, 'tags': ['tag1']}
        })
        
        mock_worker = MagicMock()
        mock_worker.add_batch_to_queue = AsyncMock()
        mock_worker.start_worker = AsyncMock()
        
        mp.setattr('app.services.playlist_service.youtube_service', mock_yt)
        mp.setattr('app.services.playlist_service.processing_worker', mock_worker)
        
        service = PlaylistService(mock_db)
        success, message, data = await service.import_playlist("https://youtube.com/list=test", "Easy", "admin1")
        
        assert success is True
        # Verify that the course_doc inserted has the video thumbnail, not the landscape one
        args, kwargs = mock_db.courses.insert_one.call_args
        inserted_doc = args[0]
        assert inserted_doc['thumbnail'] == 'https://working-thumb.jpg'
        assert inserted_doc['thumbnail'] != 'https://i9.ytimg.com/landscape_maxresdefault.jpg'
