import logging
import os
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .core.database import create_tables
from .core.config import settings
# Create tables
create_tables()

app = FastAPI(
    title="HH Job Application API", 
    version="2.0.0",
    description="API для автоматизации откликов на вакансии с HH"
)

logger.info("=== ENVIRONMENT DEBUG ===")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f".env.development exists: {os.path.exists('.env.development')}")
logger.info(f"ROBOKASSA_TEST_MODE from settings: {settings.ROBOKASSA_TEST_MODE}")
logger.info(f"DATABASE_URL: {'SET' if settings.DATABASE_URL else 'NOT SET'}")
logger.info("========================")

from .api.v1 import auth, vacancy, payment, user, saved_searches, stats
from .core.http_client import HTTPClient

# User-Agent Middleware для всех исходящих запросов
class UserAgentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Это middleware для входящих запросов, но мы можем использовать его для логирования
        response = await call_next(request)
        return response

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await HTTPClient.close()
    logger.info("HTTP client closed")

# Статический список origins для разработки и продакшена
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # Добавил запятую
    "https://hhagent.ru",
    "http://hh_frontend:3000",  # Для связи между контейнерами
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth.router)
app.include_router(vacancy.router)
app.include_router(payment.router)
app.include_router(user.router)
app.include_router(saved_searches.router)
app.include_router(stats.router)

@app.get("/")
async def root():
    return {
        "message": "HH Job Application API v2.0",
        "docs": "/docs",
        "features": [
            "OAuth авторизация через HH",
            "Поиск вакансий с полным текстом",
            "Генерация сопроводительных писем",
            "Система кредитов",
            "Оплата через Робокасса"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/cors-test")
async def cors_test():
    return {"message": "CORS working", "origins": origins}