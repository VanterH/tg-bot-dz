.PHONY: help build up down logs test init

help:
	@echo "Commands:"
	@echo "  make build  - Build Docker images"
	@echo "  make up     - Start all services"
	@echo "  make down   - Stop all services"
	@echo "  make logs   - View logs"
	@echo "  make test   - Run tests"
	@echo "  make init   - Initialize database"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	pytest tests/ -v --cov=.

init:
	docker-compose exec bot python -c "from database.db import init_db; init_db()"
	docker-compose exec bot python -c "from database.models import Base; from database.db import engine; Base.metadata.create_all(engine)"

migrate:
	docker-compose exec bot alembic upgrade head

shell:
	docker-compose exec bot python