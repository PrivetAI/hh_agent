# ————————————————
# 1) Стадия сборки зависимостей
# ————————————————
FROM python:3.11-slim AS builder

# Задаём переменные окружения для корректной установки пакетов
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Системные зависимости для сборки «тяжёлых» пакетов
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только список зависимостей, чтобы слои кэша работали эффективно
COPY requirements.txt .

# Устанавливаем зависимости в /usr/local — так они попадут в финальный образ
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники приложения
COPY . .

# ————————————————
# 2) Минимальный финальный образ
# ————————————————
FROM python:3.11-slim

# Переносим готовые пакеты из builder’а
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Если нужно, создаём непривилегированного пользователя
RUN groupadd -r app && useradd --no-log-init -r -g app app \
    && chown -R app:app /app

USER app
WORKDIR /app

# Открываем порт
EXPOSE 8000

# В проде лучше использовать gunicorn с UvicornWorker вместо --reload
CMD ["gunicorn", "app.main:app", \
      "-k", "uvicorn.workers.UvicornWorker", \
      "--bind", "0.0.0.0:8000", \
      "--workers", "4", \
      "--log-level", "info"]
