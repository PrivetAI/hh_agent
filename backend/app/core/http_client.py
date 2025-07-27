# app/core/http_client.py
import httpx
from typing import Optional
from contextlib import asynccontextmanager
import logging
from .config import settings

logger = logging.getLogger(__name__)

class HTTPClient:
    _instance: Optional[httpx.AsyncClient] = None
    
    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._instance is None:
            cls._instance = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=60.0,
                    read=60.0, 
                    write=60.0,
                    pool=60.0
                ),
                headers={
                    "User-Agent": f"{settings.HH_APP_NAME}/1.0 ({settings.HH_CONTACT_EMAIL})",
                    "HH-User-Agent": f"{settings.HH_APP_NAME}/1.0 ({settings.HH_CONTACT_EMAIL})"
                },
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
            )
            logger.info("HTTP client initialized")
        return cls._instance
    
    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("HTTP client closed")

    @classmethod
    @asynccontextmanager
    async def get_temp_client(cls, **kwargs):
        """Get temporary client with custom settings"""
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": f"{settings.HH_APP_NAME}/1.0 ({settings.HH_CONTACT_EMAIL})",
                "HH-User-Agent": f"{settings.HH_APP_NAME}/1.0 ({settings.HH_CONTACT_EMAIL})"
            },
            **kwargs
        )
        try:
            yield client
        finally:
            await client.aclose()
