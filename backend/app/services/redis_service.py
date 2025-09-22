import json
import redis.asyncio as redis
import os
from typing import Optional, Any
from fastapi import HTTPException

class RedisService:
    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )

    async def get_user_token(self, user_id: str) -> Optional[str]:
        """Get user's HH token"""
        token = await self.redis.get(f"token:{user_id}")
        if not token:
            return None
        return token.decode() if isinstance(token, bytes) else token

    async def set_user_token(self, user_id: str, token: str, expires_in: int = 86400):
        """Store user's HH token"""
        await self.redis.setex(f"token:{user_id}", expires_in, token)

    async def set_refresh_token(self, user_id: str, refresh_token: str):
        """Store user's refresh token (30 days)"""
        await self.redis.setex(f"refresh_token:{user_id}", 2592000, refresh_token)
    
    async def get_refresh_token(self, user_id: str) -> Optional[str]:
        """Get user's refresh token"""
        token = await self.redis.get(f"refresh_token:{user_id}")
        if not token:
            return None
        return token.decode() if isinstance(token, bytes) else token

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON-serializable data from Redis"""
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error for {key}: {e}")
            return None

    async def set_json(self, key: str, data: Any, expire: int = None):
        """Store JSON-serializable data in Redis"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            if expire:
                await self.redis.setex(key, expire, json_data)
            else:
                await self.redis.set(key, json_data)
        except Exception as e:
            print(f"Redis set error for {key}: {e}")
