# KARTASPB

Персональная GIS-система для Санкт-Петербурга и Ленинградской области.
Master Specification: [KARTASPB_AI_AGENT_SPEC.md](KARTASPB_AI_AGENT_SPEC.md).

## Текущий этап

SPRINT 0 — Repository & Architecture завершён и принят в Docker/PostGIS.
SPRINT 1 — минимальная карта Санкт-Петербурга на MapLibre GL JS:
нажмите на мятную demo-точку, чтобы открыть React-карточку; закройте её кнопкой ×.
Стек карты: MapLibre GL JS + OSM/open geodata + GeoJSON/PostGIS.
Демонстрационная точка не является реальным городским объектом и не сохраняется в БД.

## Запуск

Нужен Docker с Compose v2. Из корня репозитория:

```bash
docker compose up --build --wait
```

Команда использует локальные значения по умолчанию, поэтому копировать
`.env.example` для первого запуска не требуется. Для собственной конфигурации
скопируйте его в `.env` и измените значения. Первый запуск требует интернета для
загрузки образов и зависимостей.
В SPRINT 1 бесплатная development-подложка OpenFreeMap требует интернета для
стиля и тайлов. Конфигурация источника: `frontend/src/config/map.ts`;
условия и attribution: [источники данных](docs/data-sources.md).

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
docker compose run --rm backend ruff format --check .
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
