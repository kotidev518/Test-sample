
import os
import sys
from firebase_admin import storage

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_firebase

def apply_cors():
    print("Applying CORS configuration...", flush=True)
    
    # Init Firebase
    init_firebase()
    
    bucket = storage.bucket()
    print(f"Current CORS: {bucket.cors}", flush=True)
    
    # CORS Config
    cors_config = [
        {
            "origin": ["http://localhost:3000"],
            "responseHeader": ["Content-Type"],
            "method": ["GET","POST" "HEAD", "DELETE", "OPTIONS"],
            "maxAgeSeconds": 3600
        }
    ]
            
    print(f"New CORS Config: {cors_config}", flush=True)
    
    try:
        bucket.cors = cors_config
        bucket.patch()
        
        print("CORS configuration applied successfully.", flush=True)
        print(f"Updated CORS: {bucket.cors}", flush=True)
        
    except Exception as e:
        print(f"Error applying CORS: {e}", flush=True)

if __name__ == "__main__":
    apply_cors()
