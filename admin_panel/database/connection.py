from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем URL базы данных из .env или используем значения по умолчанию
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_bot_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

# Формируем URL для подключения
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Включи True для отладки SQL запросов
    pool_size=5,
    max_overflow=10
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """Dependency для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Создание всех таблиц в БД"""
    from models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Закрытие соединения с БД"""
    await engine.dispose()