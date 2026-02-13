import pytest
from app.services.gemini_service import GeminiService
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.fixture
def gemini_service():
    with patch('app.services.gemini_service.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test_key"
        service = GeminiService()
        return service

@pytest.mark.asyncio
async def test_generate_topics_success(gemini_service):
    # Mocking the _call_gemini internal method
    with patch.object(GeminiService, '_call_gemini', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '["Python", "Programming", "Testing"]'
        
        topics = await gemini_service.generate_topics("Test Video", "This is a test")
        
        assert topics == ["Python", "Programming", "Testing"]
        mock_call.assert_called_once()
        # Verify prompt contains title
        assert "Test Video" in mock_call.call_args[0][0]

@pytest.mark.asyncio
async def test_generate_topics_fallback(gemini_service):
    with patch.object(GeminiService, '_call_gemini', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("API Error")
        
        # Should fallback to keyword extraction from title
        topics = await gemini_service.generate_topics("Python Programming Tutorial")
        
        assert "Python" in topics or "Programming" in topics
        assert len(topics) > 0

@pytest.mark.asyncio
async def test_generate_quiz_success(gemini_service):
    with patch.object(GeminiService, '_call_gemini', new_callable=AsyncMock) as mock_call:
        mock_json_response = '[{"question": "What is unit testing?", "options": ["A", "B", "C", "D"], "correct_answer": 0}]'
        mock_call.return_value = mock_json_response
        
        quiz = await gemini_service.generate_quiz("Title", "Transcript", ["Topic"], num_questions=1)
        
        assert len(quiz) == 1
        assert quiz[0]["question"] == "What is unit testing?"
        assert quiz[0]["correct_answer"] == 0

@pytest.mark.asyncio
async def test_ask_video_chatbot_greeting(gemini_service):
    # This one doesn't even call Gemini if it's a greeting
    response = await gemini_service.ask_video_chatbot("User", "Video", "Transcript", "Hi")
    assert "hi user" in response.lower()
    assert "what would you like me to answer?" in response.lower()
