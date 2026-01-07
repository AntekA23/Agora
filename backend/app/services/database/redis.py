import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    """Redis connection manager."""

    client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()

    def get_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self.client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self.client


redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    """Dependency to get Redis client."""
    return redis_client.get_client()
