import pytest
from unittest.mock import MagicMock, patch

from mongomock_motor import AsyncMongoMockClient

@pytest.fixture
def mock_db():
    mock_client = AsyncMongoMockClient()
    mock_database = mock_client.test_db
    
    # Patch the DatabaseSessionManager and global db for backward compatibility
    with patch('app.db.session.db_manager.get_db', return_value=mock_database), \
         patch('app.database.db', mock_database), \
         patch('app.services.processing_queue_service.db', mock_database):
        # We also need to handle the fact that some routers might have had 'db' patched in tests
        # or were using 'from ..database import db'
        yield mock_database

@pytest.fixture
def mock_firebase_auth():
    with patch('firebase_admin.auth.verify_id_token') as mock:
        mock.return_value = {
            'uid': 'test_uid',
            'email': 'test@example.com'
        }
        yield mock

@pytest.fixture
def mock_firebase():
    with patch('app.database.db') as mock_db, \
         patch('app.database.init_firebase') as mock_init:
        yield {
            'db': mock_db,
            'init': mock_init
        }

@pytest.fixture
def mock_gemini_service():
    with patch('app.services.gemini_service.gemini_service') as mock:
        yield mock
