import pytest
from app.utils import get_video_url, hash_password, verify_password, create_token
from unittest.mock import patch, MagicMock

def test_get_video_url_http():
    url = "https://www.youtube.com/watch?v=123"
    assert get_video_url(url) == url

def test_get_video_url_gs():
    # We need to mock the storage.bucket() call inside get_video_url
    with patch('app.utils.storage.bucket') as mock_bucket:
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://signed-url.com"
        mock_bucket.return_value.blob.return_value = mock_blob
        
        url = "gs://bucket-name/folder/video.mp4"
        result = get_video_url(url)
        assert result == "https://signed-url.com"
        mock_bucket.return_value.blob.assert_called_with("folder/video.mp4")

def test_get_video_url_empty():
    assert get_video_url("") == ""

def test_password_hashing():
    password = "TestPassword@123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_create_token():
    with patch('app.utils.settings') as mock_settings:
        mock_settings.JWT_SECRET = "test_secret"
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.JWT_EXPIRATION_HOURS = 24
        
        token = create_token("user123")
        assert isinstance(token, str)
        assert len(token) > 0
