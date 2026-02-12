from arq import create_pool
from arq.connections import RedisSettings
from .config import settings

redis_pool = None

async def get_redis_pool():
    """Get or create the Redis connection pool for ARQ"""
    global redis_pool
    if redis_pool is None:
        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return redis_pool

async def enqueue_quiz_job(video_id: str):
    """
    Enqueue a quiz generation job into ARQ.
    Achieves <15ms latency in API by offloading work to background.
    """
    pool = await get_redis_pool()
    await pool.enqueue_job('generate_quiz_task', video_id)
    print(f"📥 Enqueued quiz generation job for video: {video_id}")

async def close_redis_pool():
    """Graceful shutdown of the Redis pool"""
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None
