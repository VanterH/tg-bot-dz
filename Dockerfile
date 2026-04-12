FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

# 🔴 ПРОСТО ЗАПУСКАЕМ - без создания .env
CMD ["sh", "-c", "python -m bot.main & uvicorn web_admin.simple_app:app --host 0.0.0.0 --port 8000"]
