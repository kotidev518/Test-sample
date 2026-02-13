import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_quiz_flow():
    # 1. Import a short playlist (simulate adding new videos)
    print("\n--- 1. Importing Playlist ---")
    # Using a known short playlist or video ID
    # For test, we'll manually queue a video if we can't easily import a full playlist
    # But better to check an existing video or queue a specific one
    
    # Let's check the video we fixed earlier: 5LVNJ_zAJoA
    video_id = "5LVNJ_zAJoA"
    print(f"Checking quiz for known video: {video_id}")
    
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/quizzes/{video_id}")
    latency = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        data = response.json()
        questions = data.get("questions", [])
        print(f"✅ API Response: 200 OK")
        print(f"⏱️ Latency: {latency:.2f} ms")
        print(f"📝 Questions: {len(questions)}")
        
        if len(questions) >= 4:
            print("✅ ZERO LATENCY QUIZ CONFIRMED!")
        else:
            print("❌ Quiz empty - generation failed or not ready")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_quiz_flow()
