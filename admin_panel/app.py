from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Импорт роутеров
from routers import auth, dashboard, bookings, schedule, clients, reports, settings

# Импорт работы с БД
from database import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск: создаём таблицы
    await init_db()
    print("✅ База данных инициализирована")
    yield
    # Остановка: закрываем соединения
    await close_db()
    print("👋 Соединение с БД закрыто")

# Создаём приложение
app = FastAPI(
    title="Admin Panel for Telegram Bot",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(bookings.router)
app.include_router(schedule.router)
app.include_router(clients.router)
app.include_router(reports.router)
app.include_router(settings.router)

# Корневой маршрут - перенаправление на админку
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)