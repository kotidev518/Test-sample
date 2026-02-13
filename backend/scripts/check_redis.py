import asyncio
import redis
from app.config import settings

async def check_redis():
    print(f"Connecting to Redis at {settings.REDIS_URL}...")
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        ping = r.ping()
        if ping:
            print(" Redis is UP and running!")
        else:
            print(" Redis ping failed.")
    except Exception as e:
        print(f" Could not connect to Redis: {e}")
        print("\nPlease ensure Redis is installed and running on your system.")
        print("Note: If you are on Windows, you might need to start Redis via WSL or the 'Redis' service.")

if __name__ == "__main__":
    asyncio.run(check_redis())
