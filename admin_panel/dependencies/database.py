from database.connection import AsyncSessionLocal

async def get_db():
    """Dependency для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session