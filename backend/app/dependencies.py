from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from .database import db

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Firebase ID token and return user from database"""
    try:
        # Verify the Firebase ID token
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        
        if not firebase_uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Look up user by firebase_uid first, then by email as fallback
        user = await db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
        
        if not user and email:
            # Try finding by email (for users created before firebase migration)
            user = await db.users.find_one({"email": email}, {"_id": 0})
            if user:
                # Update user with firebase_uid for future lookups
                await db.users.update_one(
                    {"email": email},
                    {"$set": {"firebase_uid": firebase_uid}}
                )
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found. Please register first.")
        
        return user
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired")
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_admin_user(user = Depends(get_current_user)):
    """Verify that the current user is an admin"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=403, 
            detail="Admin access required"
        )
    return user
