# app/core/http_client.py
import httpx
from typing import Optional
from .config import settings

class HTTPClient:
    _instance: Optional[httpx.AsyncClient] = None
    
    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._instance is None:
            cls._instance = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=30.0,
                    write=30.0,
                    pool=30.0
                ),
                headers={
                    "User-Agent": "HH-User-Agent",
                    "HH-User-Agent": f"{settings.HH_APP_NAME}/1.0 ({settings.HH_CONTACT_EMAIL})"
                }
            )
        return cls._instance
    
    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None