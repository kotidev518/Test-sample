from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings

class DatabaseSessionManager:
    def __init__(self):
        self._client: AsyncIOMotorClient = None
        self._db = None

    def init_db(self):
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.MONGO_URL)
            self._db = self._client[settings.DB_NAME]

    async def close_db(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    def get_db(self):
        if self._db is None:
            self.init_db()
        return self._db

db_manager = DatabaseSessionManager()

async def get_db():
    return db_manager.get_db()
