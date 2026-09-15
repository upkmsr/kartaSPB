# KARTASPB

Персональная GIS-система для Санкт-Петербурга и Ленинградской области.
Master Specification: [KARTASPB_AI_AGENT_SPEC.md](KARTASPB_AI_AGENT_SPEC.md).

## Текущий этап

SPRINT 0 — Repository & Architecture. Реализован каркас, приёмка Docker/PostGIS
ожидает окружения с Docker. Карта начинается в SPRINT 1 и пока не реализована.
Стек карты зафиксирован: MapLibre GL JS + OSM/open geodata + GeoJSON/PostGIS.

## Запуск

Нужен Docker с Compose v2. Из корня репозитория:

```bash
cp .env.example .env
docker compose up --build
```

Также поддерживается `docker compose up` с локальными значениями по умолчанию.
Первый запуск требует интернета для образов и зависимостей.

- Интерфейс: http://localhost:5173
- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/api/health/live
- Readiness (PostGIS и миграция): http://localhost:8000/api/health/ready

Compose ждёт БД, выполняет `alembic upgrade head`, затем запускает API и frontend.
БД хранится в named volume, порт БД наружу не публикуется.
Остановка: `docker compose down` (данные сохраняются).
Пароль по умолчанию предназначен только для локальной разработки.

## Проверки

```bash
docker compose run --rm backend pytest
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -m integration
docker compose run --rm backend ruff check .
docker compose run --rm backend mypy app
cd frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
```

См. [разработка](docs/development.md), [архитектура](docs/architecture.md),
[отчёт спринта](docs/sprint-0.md), [изменения](CHANGELOG.md).
