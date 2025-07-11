from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/hhapp"
    REDIS_URL: str = "redis://localhost:6379"
    HH_CLIENT_ID: str = ""
    HH_CLIENT_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    ROBOKASSA_MERCHANT_LOGIN: str = ""
    ROBOKASSA_PASSWORD_1: str = ""
    ROBOKASSA_PASSWORD_2: str = ""
    ROBOKASSA_TEST_MODE: bool = True
    ROBOKASSA_TEST_PASSWORD_1: str = ""
    ROBOKASSA_TEST_PASSWORD_2: str = ""
    HH_BATCH_SIZE: int = 5
    HH_BATCH_DELAY: float = 1.0
    HH_RETRY_COUNT: int = 3
    
    class Config:
        env_file = os.getenv('env_file', '.env.development')
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()   