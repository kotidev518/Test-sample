from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..dependencies import get_current_user, security, get_auth_service
from ..schemas import UserProfile, UserProfileCreate
from ..services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserProfile)
async def register(
    user_data: UserProfileCreate, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create or update user profile after Firebase authentication.
    """
    return await auth_service.register_or_login(credentials.credentials, user_data)

@router.get("/me", response_model=UserProfile)
async def get_me(user = Depends(get_current_user)):
    return UserProfile(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        initial_level=user.get('initial_level', 'Easy'),
        role=user.get('role', 'user'),
        created_at=user['created_at']
    )

@router.post("/login", response_model=UserProfile)
async def login(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with Firebase token.
    """
    return await auth_service.register_or_login(credentials.credentials)

@router.post("/google-login", response_model=UserProfile)
async def google_login(
    user_data: UserProfileCreate, 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Handle Google Sign-In.
    """
    return await auth_service.register_or_login(credentials.credentials, user_data)
