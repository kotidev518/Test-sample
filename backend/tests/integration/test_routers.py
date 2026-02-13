import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer dummy_token"}

@pytest.fixture
async def client(mock_db):
    # Mocking initialization of services at startup to avoid external calls
    with patch('app.main.init_firebase'), \
         patch('app.main.init_embedding_service'), \
         patch('app.main.ensure_indexes'):
        
        # Override dependencies to use the mock_db
        from app.dependencies import get_current_user, get_db
        
        async def mock_get_db():
            return mock_db

        async def mock_get_current_user():
            user = await mock_db.users.find_one({"firebase_uid": "test_uid"})
            if not user:
                return {
                    "id": "default_id",
                    "email": "test@example.com",
                    "name": "Default User",
                    "role": "student",
                    "created_at": "2024-01-01"
                }
            return user

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
            app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Course Platform API"}

@pytest.mark.asyncio
async def test_auth_register_success(client, mock_db, mock_firebase_auth, auth_header):
    # Mocking uid generation
    with patch('app.services.auth_service.uuid4', return_value="user_123"):
        register_data = {
            "name": "Integration User",
            "initial_level": "Easy"
        }
        
        # In register, verify_id_token is called with the credentials from the header
        response = await client.post("/api/auth/register", json=register_data, headers=auth_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com" # From mock_firebase_auth return_value
        assert data["name"] == "Integration User"
        
        # Verify user in mock DB
        user = await mock_db.users.find_one({"firebase_uid": "test_uid"})
        assert user is not None
        assert user["name"] == "Integration User"

@pytest.mark.asyncio
async def test_get_courses_empty(client, mock_db, mock_firebase_auth, auth_header):
    # Seed user
    await mock_db.users.insert_one({
        "id": "user_123",
        "firebase_uid": "test_uid",
        "email": "test@example.com",
        "name": "Test User",
        "role": "student",
        "created_at": "2024-01-01"
    })
    
    response = await client.get("/api/courses", headers=auth_header)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_courses_with_data(client, mock_db, mock_firebase_auth, auth_header):
    # Seed user
    await mock_db.users.insert_one({
        "id": "user_123",
        "firebase_uid": "test_uid",
        "email": "test@example.com",
        "name": "Test User",
        "role": "student",
        "created_at": "2024-01-01"
    })
    
    # Seed course
    await mock_db.courses.insert_one({
        "id": "course_1",
        "title": "Test Course",
        "description": "Desc",
        "difficulty": "Easy",
        "topics": ["T1"],
        "thumbnail": "thumb.jpg",
        "video_count": 0,
        "imported_at": "2024-01-01",
        "imported_by": "admin"
    })
    
    response = await client.get("/api/courses", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test Course"
