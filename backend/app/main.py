from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import create_tables
from .api.v1 import auth, vacancy, payment, user

# Создание таблиц базы данных
create_tables()

app = FastAPI(
    title="HH Job Application API", 
    version="2.0.0",
    description="API для автоматизации откликов на вакансии с HH"
)

# Список разрешённых источников (origins)
origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://hhagent.ru",               # Добавлено продакшн-домен
    "http://hh_frontend:3000",          # Docker контейнеры
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Можно оставить *, это нормально
    allow_headers=["*"],  # Разрешаем любые заголовки
)

# Роуты с префиксом /api
app.include_router(auth.router, prefix="/api")
app.include_router(vacancy.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(user.router, prefix="/api")

# Главная страница API
@app.get("/api/")
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

# Healthcheck
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Проверка CORS
@app.get("/api/cors-test")
async def cors_test():
    return {"message": "CORS working", "origins": origins}
