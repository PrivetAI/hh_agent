from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/hhapp"
    REDIS_URL: str = "redis://localhost:6379"
    HH_CLIENT_ID: str = ""
    HH_CLIENT_SECRET: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    ROBOKASSA_MERCHANT_LOGIN: str = "hhbot"
    ROBOKASSA_PASSWORD_1: str = ""
    ROBOKASSA_PASSWORD_2: str = ""
    ROBOKASSA_TEST_MODE: bool = Field(default=True)
    ROBOKASSA_TEST_PASSWORD_1: str = ""  # Значение по умолчанию для dev
    ROBOKASSA_TEST_PASSWORD_2: str = ""  # Значение по умолчанию для dev
    HH_BATCH_SIZE: int = 1
    HH_BATCH_DELAY: float = 1.0
    HH_RETRY_COUNT: int = 3
    HH_APP_NAME: str = "hh_agent"
    HH_CONTACT_EMAIL: str = "support@hhagent.ru"
    @field_validator('ROBOKASSA_TEST_MODE', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Разрешаем дополнительные поля из .env файла
        extra = 'ignore'
settings = Settings()