"""
Initialize MongoDB Atlas Collections
This script creates all required collections with proper indexes.
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

async def init_collections():
    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME", "learning_platform")
    
    print(f"🔄 Connecting to MongoDB Atlas...")
    
    try:
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # Ping to verify connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas!")
        
        # Define all collections with their indexes
        collections_config = {
            "users": [
                {"keys": [("id", 1)], "unique": True},
                {"keys": [("firebase_uid", 1)], "unique": True},
                {"keys": [("email", 1)], "unique": True}
            ],
            "courses": [
                {"keys": [("id", 1)], "unique": True}
            ],
            "videos": [
                {"keys": [("id", 1)], "unique": True},
                {"keys": [("course_id", 1)], "unique": False}
            ],
            "quizzes": [
                {"keys": [("id", 1)], "unique": True},
                {"keys": [("video_id", 1)], "unique": False}
            ],
            "user_progress": [
                {"keys": [("user_id", 1), ("video_id", 1)], "unique": True}
            ],
            "quiz_results": [
                {"keys": [("user_id", 1), ("quiz_id", 1)], "unique": False},
                {"keys": [("user_id", 1)], "unique": False}
            ],
            "mastery_scores": [
                {"keys": [("user_id", 1), ("topic", 1)], "unique": True}
            ]
        }
        
        print(f"\n📦 Initializing collections in '{db_name}'...\n")
        
        for collection_name, indexes in collections_config.items():
            print(f"📂 Creating collection: {collection_name}")
            
            # Create collection if it doesn't exist
            # We do this by inserting and then deleting a dummy document
            collection = db[collection_name]
            
            # Check if collection exists
            existing_collections = await db.list_collection_names()
            if collection_name not in existing_collections:
                # Create by inserting a dummy doc
                await collection.insert_one({"_init": True})
                await collection.delete_one({"_init": True})
                print(f"   ✅ Collection created")
            else:
                print(f"   ℹ️  Collection already exists")
            
            # Create indexes
            for idx_config in indexes:
                try:
                    await collection.create_index(
                        idx_config["keys"],
                        unique=idx_config["unique"]
                    )
                    keys_str = ", ".join([f"{k[0]}" for k in idx_config["keys"]])
                    unique_str = "(unique)" if idx_config["unique"] else ""
                    print(f"   📑 Index on [{keys_str}] {unique_str}")
                except Exception as e:
                    print(f"   ⚠️  Index error: {e}")
        
        # Verify all collections
        print(f"\n✅ Verification - Collections in '{db_name}':")
        collections = await db.list_collection_names()
        for col in sorted(collections):
            if not col.startswith("_"):  # Skip test collection
                count = await db[col].count_documents({})
                print(f"   📂 {col}: {count} documents")
        
        # Clean up test collection if it exists
        if "_connection_test" in collections:
            await db["_connection_test"].drop()
            print("\n🧹 Cleaned up test collection")
        
        print("\n🎉 All collections initialized successfully!")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(init_collections())
