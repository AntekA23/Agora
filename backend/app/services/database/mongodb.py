from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class MongoDB:
    """MongoDB connection manager."""

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Connect to MongoDB."""
        # Log connection info (mask password for security)
        uri = settings.MONGODB_URI
        masked_uri = uri.split("@")[-1] if "@" in uri else uri
        print(f"[MongoDB] Connecting to: ...@{masked_uri}")
        print(f"[MongoDB] Database name: {settings.MONGODB_DB_NAME}")

        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB_NAME]

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()

    def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db


mongodb = MongoDB()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance."""
    return mongodb.get_db()
