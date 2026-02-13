import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

# Add the project root to sys.path to allow imports from 'app'
# Running from repo root: python backend/scripts/create_admin.py
# Root should be 'backend' folder
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Load .env file from the backend directory
load_dotenv(os.path.join(root_dir, ".env"))

from firebase_admin import auth as firebase_auth
from app.database import init_firebase
from app.db.session import db_manager
from app.schemas import UserDB

# ==========================================
# CONFIGURE ADMIN CREDENTIALS HERE
# ==========================================
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "Admin@123"
ADMIN_NAME = "System Admin"
# ==========================================

async def create_admin():
    print(f" Starting Admin Account Creation for: {ADMIN_EMAIL}")
    
    # Initialize Firebase and MongoDB
    init_firebase()
    db_manager.init_db()
    db = db_manager.get_db()
    
    try:
        # 1. Create or get user in Firebase Auth
        try:
            user = firebase_auth.get_user_by_email(ADMIN_EMAIL)
            print(f"✅ User already exists in Firebase (UID: {user.uid}). Updating password...")
            firebase_auth.update_user(
                user.uid,
                password=ADMIN_PASSWORD,
                display_name=ADMIN_NAME
            )
            firebase_uid = user.uid
        except firebase_auth.UserNotFoundError:
            user = firebase_auth.create_user(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                display_name=ADMIN_NAME
            )
            print(f" Created new user in Firebase (UID: {user.uid})")
            firebase_uid = user.uid
        except Exception as e:
            print(f" Error with Firebase Auth: {e}")
            return

        # 2. Sync with MongoDB
        existing_user = await db.users.find_one({"email": ADMIN_EMAIL})
        
        if existing_user:
            print(f"  Updating existing user in MongoDB to admin role...")
            await db.users.update_one(
                {"email": ADMIN_EMAIL},
                {
                    "$set": {
                        "role": "admin",
                        "firebase_uid": firebase_uid,
                        "name": ADMIN_NAME,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            print(" User updated to admin successfully.")
        else:
            print(f" Creating new admin user record in MongoDB...")
            user_doc = {
                "id": str(uuid4()),
                "firebase_uid": firebase_uid,
                "email": ADMIN_EMAIL,
                "name": ADMIN_NAME,
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user_doc)
            print(" New admin user record created successfully.")

        print("\n Admin account is ready!")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        print("You can now login at /admin-login (once implemented)")

    except Exception as e:
        print(f" An unexpected error occurred: {e}")
    finally:
        await db_manager.close_db()

if __name__ == "__main__":
    asyncio.run(create_admin())
