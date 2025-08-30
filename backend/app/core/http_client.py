# app/core/http_client.py
import httpx
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
from .config import settings

logger = logging.getLogger(__name__)

class HTTPClient:
    _instance: Optional[httpx.AsyncClient] = None
    _ai_client: Optional[httpx.AsyncClient] = None  # Separate client for AI requests
    
    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Get main HTTP client for HH API requests"""
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
                limits=httpx.Limits(
                    max_keepalive_connections=50,
                    max_connections=100,
                    keepalive_expiry=60  # Close idle connections after 30s
                )
            )
            logger.info("Main HTTP client initialized")
        return cls._instance
    
    @classmethod
    def get_ai_client(cls) -> httpx.AsyncClient:
        """Get separate HTTP client for AI requests with different timeout settings"""
        if cls._ai_client is None:
            cls._ai_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=60.0,
                    read=120.0,    # Longer timeout for AI requests
                    write=10.0,
                    pool=120.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=10,  # Less connections for AI
                    max_connections=20,
                    keepalive_expiry=60
                )
            )
            logger.info("AI HTTP client initialized")
        return cls._ai_client
    
    @classmethod
    async def close(cls):
        """Close all clients"""
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("Main HTTP client closed")
        
        if cls._ai_client:
            await cls._ai_client.aclose()
            cls._ai_client = None
            logger.info("AI HTTP client closed")

    @classmethod
    @asynccontextmanager
    async def get_temp_client(cls, timeout: int = 30, **kwargs):
        """Get temporary client with custom settings"""
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
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