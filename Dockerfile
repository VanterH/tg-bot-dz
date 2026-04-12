FROM python:3.11-slim

WORKDIR /app

# Аргументы для сборки (берутся из GitHub Secrets)
ARG BOT_TOKEN
ARG ADMIN_TELEGRAM_ID
ARG EXPERT_TELEGRAM_IDS
ARG DATABASE_URL
ARG DB_PASSWORD
ARG YANDEX_FOLDER_ID
ARG YANDEX_API_KEY
ARG SECRET_KEY
ARG RAG_MOCK_MODE

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# 🔴 СОЗДАЕМ .env ФАЙЛ ИЗ АРГУМЕНТОВ
RUN echo "BOT_TOKEN=${BOT_TOKEN}" > .env && \
    echo "ADMIN_TELEGRAM_ID=${ADMIN_TELEGRAM_ID}" >> .env && \
    echo "EXPERT_TELEGRAM_IDS=${EXPERT_TELEGRAM_IDS}" >> .env && \
    echo "DATABASE_URL=${DATABASE_URL}" >> .env && \
    echo "DB_PASSWORD=${DB_PASSWORD}" >> .env && \
    echo "YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}" >> .env && \
    echo "YANDEX_API_KEY=${YANDEX_API_KEY}" >> .env && \
    echo "SECRET_KEY=${SECRET_KEY}" >> .env && \
    echo "RAG_MOCK_MODE=${RAG_MOCK_MODE}" >> .env && \
    echo "YANDEX_MODEL=yandexgpt-lite" >> .env && \
    echo "RAG_TOP_K=5" >> .env && \
    echo "RAG_CONFIDENCE_THRESHOLD=0.6" >> .env

# Проверяем что .env создался (для отладки)
RUN cat .env

RUN mkdir -p uploads

EXPOSE 8000

CMD ["sh", "-c", "python -m bot.main & uvicorn web_admin.simple_app:app --host 0.0.0.0 --port 8000"]
