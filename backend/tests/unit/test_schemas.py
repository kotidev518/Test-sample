import pytest
from app.schemas import UserRegister, UserLogin, PASSWORD_ERROR_MESSAGE
from pydantic import ValidationError

def test_user_register_schema_valid():
    data = {
        "email": "test@example.com",
        "password": "Password@123",
        "name": "Test User"
    }
    user = UserRegister(**data)
    assert user.email == data["email"]
    assert user.name == data["name"]

def test_user_register_schema_invalid_password():
    data = {
        "email": "test@example.com",
        "password": "weak",
        "name": "Test User"
    }
    with pytest.raises(ValidationError) as exc:
        UserRegister(**data)
    assert PASSWORD_ERROR_MESSAGE in str(exc.value)

def test_user_login_schema():
    data = {
        "email": "test@example.com",
        "password": "Password@123"
    }
    login = UserLogin(**data)
    assert login.email == data["email"]
