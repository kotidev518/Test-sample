from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional
from fastapi import HTTPException
from firebase_admin import auth as firebase_auth
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import UserProfile, UserProfileCreate, UserDB
from app.utils.email_validator import validate_email_domain

class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def register_or_login(self, id_token: str, user_data: Optional[UserProfileCreate] = None) -> UserProfile:
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            
            if not firebase_uid or not email:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check if user already exists in our database
            user = await self.db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})
            
            # If user is NOT in our database, we MUST validate their domain before proceeding
            # This covers both standard registration and first-time Google logins.
            if not user:
                # First check if they exist by email (migration case)
                existing_by_email = await self.db.users.find_one({"email": email}, {"id": 1})
                if not existing_by_email:
                    # Brand new user -> strict domain validation
                    try:
                        validate_email_domain(email)
                    except HTTPException:
                        raise
                    except Exception:
                        raise HTTPException(status_code=400, detail="enter a valid domain")
            
            # Proceed with login/lookup logic
            if user:
                return self._map_to_profile(user)
            
            # Check by email for migration
            user = await self.db.users.find_one({"email": email}, {"_id": 0})
            if user:
                await self.db.users.update_one({"email": email}, {"$set": {"firebase_uid": firebase_uid}})
                return self._map_to_profile(user)
            
            # Create new user
            if not user_data:
                # This might happen during login for a non-existent user
                raise HTTPException(status_code=404, detail="User not found. Please register first.")
                
            user_id = str(uuid4())
            user_doc = UserDB(
                id=user_id,
                firebase_uid=firebase_uid,
                email=email,
                name=user_data.name,
                initial_level=user_data.initial_level or "Easy",
                created_at=datetime.now(timezone.utc).isoformat()
            )
            await self.db.users.insert_one(user_doc.model_dump())
            return user_doc
            
        except firebase_auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Token expired")
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[dict]:
        return await self.db.users.find_one({"firebase_uid": firebase_uid}, {"_id": 0})

    def _map_to_profile(self, user: dict) -> UserProfile:
        return UserProfile(
            id=user['id'],
            email=user['email'],
            name=user['name'],
            initial_level=user.get('initial_level', 'Easy'),
            role=user.get('role', 'user'),
            created_at=user['created_at']
        )
