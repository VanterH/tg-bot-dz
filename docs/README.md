# Документация проекта

## 📋 Содержание

1. [Архитектура](#архитектура)
2. [API Endpoints](#api-endpoints)
3. [База данных](#база-данных)
4. [Развертывание](#развертывание)
5. [Устранение неполадок](#устранение-неполадок)

## Архитектура

Проект состоит из 4 основных компонентов:

### 1. Telegram Bot (`bot/`)
- `main.py` - Точка входа, инициализация бота
- `handlers.py` - Обработчики команд и callback'ов
- `keyboards.py` - Клавиатуры для бота
- `states.py` - FSM состояния
- `utils.py` - Вспомогательные функции

### 2. Web Admin Panel (`web_admin/`)
- `main.py` - FastAPI приложение
- `routes.py` - Маршруты API
- `templates/` - Jinja2 шаблоны
- `static/` - CSS стили

### 3. Scheduler (`scheduler/`)
- `tasks.py` - Фоновые задачи
- `runner.py` - Запуск планировщика

### 4. Database (`database/`)
- `models.py` - SQLAlchemy модели
- `db.py` - Подключение к БД

## API Endpoints

### Админ-панель
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Дашборд |
| `/login` | GET/POST | Вход |
| `/bookings` | GET | Список заявок |
| `/schedule` | GET | Расписание |
| `/clients` | GET | Клиенты |
| `/reports` | GET | Отчёты |
| `/settings` | GET | Настройки |
| `/export/excel` | GET | Экспорт Excel |
| `/export/csv` | GET | Экспорт CSV |

### API для AJAX
| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/stats` | GET | Статистика |
| `/booking/{id}` | GET | Детали заявки |
| `/confirm_booking/{id}` | POST | Подтверждение оплаты |

## База данных

### Схема
