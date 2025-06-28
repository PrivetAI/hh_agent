from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/hhapp"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # HeadHunter
    HH_CLIENT_ID: str
    HH_CLIENT_SECRET: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # Robokassa
    ROBOKASSA_MERCHANT_LOGIN: str
    ROBOKASSA_PASSWORD_1: str  # Для формирования запроса
    ROBOKASSA_PASSWORD_2: str  # Для проверки ответа
    ROBOKASSA_TEST_MODE: bool = True
    ROBOKASSA_TEST_PASSWORD_1: str = "test_password_1"
    ROBOKASSA_TEST_PASSWORD_2: str = "test_password_2"
    
    # App
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    
    # HH Rate Limiting
    HH_BATCH_SIZE: int = 5
    HH_BATCH_DELAY: float = 1.0
    HH_RETRY_COUNT: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()