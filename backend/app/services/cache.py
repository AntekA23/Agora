"""Redis caching service."""

import json
from typing import Any

from redis.asyncio import Redis

from app.services.database import get_redis


class CacheService:
    """Service for caching data in Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        await self.redis.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or self.default_ttl,
        )

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    # Cache key generators
    @staticmethod
    def company_key(company_id: str) -> str:
        return f"company:{company_id}"

    @staticmethod
    def user_key(user_id: str) -> str:
        return f"user:{user_id}"

    @staticmethod
    def analytics_key(company_id: str) -> str:
        return f"analytics:dashboard:{company_id}"


async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    redis = await get_redis()
    return CacheService(redis)
