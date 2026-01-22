"""
Script to set a user as admin in MongoDB
Usage: python set_admin.py admin@admin.com
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://TL:Aditya1234@lms.avyadxo.mongodb.net/?appName=LMS"
DB_NAME = "learning_platform"

async def set_admin(email: str):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check if user exists
    user = await db.users.find_one({"email": email})
    if not user:
        print(f"❌ User with email '{email}' not found!")
        print("\nExisting users:")
        async for u in db.users.find({}, {"email": 1, "name": 1, "role": 1}):
            role = u.get('role', 'user')
            print(f"  - {u.get('email')} ({u.get('name', 'N/A')}) - {role}")
        return
    
    # Update user role
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"role": "admin"}}
    )
    
    if result.modified_count > 0:
        print(f"✅ Successfully set '{email}' as admin!")
    else:
        print(f"ℹ️  User '{email}' is already an admin.")
    
    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = input("Enter admin email: ")
    else:
        email = sys.argv[1]
    
    asyncio.run(set_admin(email))
