"""
Test script to verify SBERT embedding system functionality
Run this after starting the backend server
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from app.services.embedding_service import embedding_service
from app.services.transcript_service import transcript_service
from app.services.processing_queue_service import processing_worker
from app.database import db


async def test_embedding_service():
    """Test embedding generation and similarity"""
    print("\n=== Testing Embedding Service ===\n")
    
    # Test 1: Generate embedding
    print("1. Testing embedding generation...")
    text1 = "Learn Python programming basics including variables, loops, and functions"
    embedding1 = await embedding_service.generate_embedding(text1)
    
    if embedding1:
        print(f"   ✓ Generated embedding ({len(embedding1)} bytes)")
    else:
        print("   ✗ Failed to generate embedding")
        return False
    
    # Test 2: Similarity computation
    print("\n2. Testing similarity computation...")
    text2 = "Python tutorial for beginners covering basic programming concepts"
    text3 = "JavaScript web development and React framework"
    
    embedding2 = await embedding_service.generate_embedding(text2)
    embedding3 = await embedding_service.generate_embedding(text3)
    
    sim_12 = await embedding_service.compute_cosine_similarity(embedding1, embedding2)
    sim_13 = await embedding_service.compute_cosine_similarity(embedding1, embedding3)
    
    print(f"   Similarity (Python vs Python tutorial): {sim_12:.4f}")
    print(f"   Similarity (Python vs JavaScript): {sim_13:.4f}")
    
    if sim_12 > sim_13:
        print("   ✓ Similarity test passed (Python texts more similar)")
    else:
        print("   ✗ Similarity test failed")
        return False
    
    return True


async def test_transcript_service():
    """Test transcript fetching with rate limiting"""
    print("\n=== Testing Transcript Service ===\n")
    
    # Test video ID (replace with a valid YouTube video ID from your course)
    test_video_id = "dQw4w9WgXcQ"  # Example video
    
    print(f"1. Fetching transcript for {test_video_id} with rate limiting...")
    print("   (This will take 2-5 seconds due to rate limiting)")
    
    import time
    start = time.time()
    
    transcript = await transcript_service.get_transcript_with_rate_limit(
        test_video_id,
        delay_range=(2, 3)  # Reduced for testing
    )
    
    elapsed = time.time() - start
    
    if transcript:
        print(f"   ✓ Transcript fetched ({len(transcript)} chars) in {elapsed:.1f}s")
        print(f"   Preview: {transcript[:100]}...")
    else:
        print(f"   ⚠️ No transcript available (took {elapsed:.1f}s)")
    
    if elapsed >= 2.0:
        print("   ✓ Rate limiting working (delay applied)")
        return True
    else:
        print("   ✗ Rate limiting may not be working")
        return False


async def test_processing_queue():
    """Test processing queue functionality"""
    print("\n=== Testing Processing Queue ===\n")
    
    # Test 1: Queue status
    print("1. Checking queue status...")
    status = await processing_worker.get_queue_status()
    print(f"   Queue status: {status}")
    
    # Test 2: Add test video to queue
    print("\n2. Adding test video to queue...")
    test_video_id = "test-video-123"
    
    success = await processing_worker.add_to_queue(test_video_id, priority=1)
    
    if success:
        print(f"   ✓ Video {test_video_id} added to queue")
    else:
        print(f"   ⚠️ Video already in queue")
    
    # Test 3: Check updated status
    print("\n3. Checking updated queue status...")
    new_status = await processing_worker.get_queue_status()
    print(f"   Updated status: {new_status}")
    
    return True


async def test_database_indexes():
    """Test database indexes"""
    print("\n=== Testing Database Indexes ===\n")
    
    print("1. Checking processing_queue indexes...")
    indexes = await db.processing_queue.index_information()
    
    required_indexes = ["status_1_priority_-1", "video_id_1"]
    found = []
    
    for idx in required_indexes:
        if idx in indexes:
            found.append(idx)
            print(f"   ✓ Index '{idx}' exists")
        else:
            print(f"   ✗ Index '{idx}' missing")
    
    print(f"\n2. Checking videos indexes...")
    video_indexes = await db.videos.index_information()
    
    if "processing_status_1" in video_indexes:
        print("   ✓ Index 'processing_status' exists")
        found.append("processing_status_1")
    else:
        print("   ✗ Index 'processing_status' missing")
    
    return len(found) >= 2


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SBERT EMBEDDING SYSTEM VERIFICATION TESTS")
    print("="*60)
    
    results = {}
    
    # Test 1: Embedding Service
    try:
        results["embedding"] = await test_embedding_service()
    except Exception as e:
        print(f"\n❌ Embedding test failed: {e}")
        results["embedding"] = False
    
    # Test 2: Transcript Service
    try:
        results["transcript"] = await test_transcript_service()
    except Exception as e:
        print(f"\n❌ Transcript test failed: {e}")
        results["transcript"] = False
    
    # Test 3: Processing Queue
    try:
        results["queue"] = await test_processing_queue()
    except Exception as e:
        print(f"\n❌ Queue test failed: {e}")
        results["queue"] = False
    
    # Test 4: Database Indexes
    try:
        results["indexes"] = await test_database_indexes()
    except Exception as e:
        print(f"\n❌ Index test failed: {e}")
        results["indexes"] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.ljust(20)}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    print("="*60 + "\n")
    
    if total_passed == total_tests:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
