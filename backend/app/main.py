from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import create_tables
from .api.v1 import auth, vacancy, payment, user

# Create tables
create_tables()

app = FastAPI(
    title="HH Job Application API", 
    version="2.0.0",
    description="API для автоматизации откликов на вакансии с HH"
)

# Статический список origins для разработки и продакшена
origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://hh-agent.robotoffice.ru",
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