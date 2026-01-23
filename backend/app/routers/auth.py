from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth

from ..database import db
from ..schemas import UserProfile, UserProfileCreate
from ..dependencies import get_current_user, security

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserProfile)
async def register(user_data: UserProfileCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Create or update user profile after Firebase authentication.
    Expects Firebase ID token in Authorization header.
    """
    try:
        # Verify the Firebase ID token
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        if not firebase_uid or not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if user already exists
        existing = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
        if existing:
            # User already registered, return existing profile
            return UserProfile(
                id=existing['id'],
                email=existing['email'],
                name=existing['name'],
                initial_level=existing.get('initial_level', 'Easy'),
                role=existing.get('role', 'user'),
                created_at=existing['created_at']
            )
        
        # Also check by email (for migration from old system)
        existing_by_email = await db.users.find_one({"email": email}, {"_id": 0})
        if existing_by_email:
            # Update existing user with firebase_uid
            await db.users.update_one(
                {"email": email},
                {"$set": {"firebase_uid": firebase_uid}}
            )
            return UserProfile(
                id=existing_by_email['id'],
                email=existing_by_email['email'],
                name=existing_by_email['name'],
                initial_level=existing_by_email.get('initial_level', 'Easy'),
                role=existing_by_email.get('role', 'user'),
                created_at=existing_by_email['created_at']
            )
        
        # Create new user
        user_id = str(uuid4())
        user_doc = {
            "id": user_id,
            "firebase_uid": firebase_uid,
            "email": email,
            "name": user_data.name,
            "initial_level": user_data.initial_level or "Easy",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(user_doc)
        
        return UserProfile(
            id=user_id,
            email=email,
            name=user_data.name,
            initial_level=user_data.initial_level or "Easy",
            created_at=user_doc["created_at"]
        )
        
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Registration error: {e}")
        import traceback
        with open("debug.log", "a") as f:
            f.write(f"Registration ERROR: {str(e)}\n")
            f.write(traceback.format_exc() + "\n")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

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
async def login(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Login with Firebase token.
    Verifies token and returns user profile.
    """
    try:
        # Verify the Firebase ID token
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token.get('uid')
        
        if not firebase_uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if user exists
        user = await db.users.find_one({"firebase_uid": firebase_uid})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return UserProfile(
            id=user['id'],
            email=user['email'],
            name=user['name'],
            initial_level=user.get('initial_level', 'Easy'),
            role=user.get('role', 'user'),
            created_at=user['created_at']
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/google-login", response_model=UserProfile)
async def google_login(user_data: UserProfileCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Handle Google Sign-In. 
    Creates user if not exists, otherwise logs them in.
    """
    # This logic is very similar to register, but specific for the Google flow semantics
    # We can reuse the register logic or call it directly, but clean separation is good.
    return await register(user_data, credentials)
