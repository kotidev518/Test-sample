"""
MongoDB Atlas Connection Test Script
Run this script to verify your MongoDB Atlas connection is working.
"""
import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

async def test_connection():
    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME", "learning_platform")
    
    print(f"🔄 Connecting to MongoDB Atlas...")
    print(f"📦 Database: {db_name}")
    
    try:
        # Create client with timeout
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        
        # Test the connection by listing databases
        db = client[db_name]
        
        # Ping the database
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"\n📂 Collections in '{db_name}':")
        if collections:
            for col in collections:
                count = await db[col].count_documents({})
                print(f"   - {col}: {count} documents")
        else:
            print("   (No collections yet - this is normal for a new database)")
        
        # Test write and read
        print("\n🧪 Testing write/read operations...")
        test_collection = db["_connection_test"]
        test_doc = {"test": True, "message": "MongoDB Atlas connection successful!"}
        
        # Insert
        result = await test_collection.insert_one(test_doc)
        print(f"   ✅ Write test passed (inserted id: {result.inserted_id})")
        
        # Read
        found = await test_collection.find_one({"test": True})
        print(f"   ✅ Read test passed (message: {found['message']})")
        
        # Cleanup
        await test_collection.delete_one({"_id": result.inserted_id})
        print("   ✅ Cleanup completed")
        
        print("\n🎉 All tests passed! Your MongoDB Atlas connection is working correctly.")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if your IP is whitelisted in MongoDB Atlas Network Access")
        print("2. Verify username/password in connection string")
        print("3. Ensure the cluster is running and not paused")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_connection())
