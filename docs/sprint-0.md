# SPRINT 0 — Repository & Architecture

## Исходное состояние

В репозитории были только README и пользовательский `KARTASPB_AI_AGENT_SPEC.md`.
Файл `AI_AGENT_SPEC.md` отсутствовал; полностью прочитан существующий Master Specification.
Кода, зависимостей, миграций и инфраструктуры не было. Ближайший незавершённый этап — 0.

## Сделано

- Структура CORE + будущие MODULES без реализации следующих спринтов.
- React/TypeScript/Vite frontend с адаптивным тёмным UI и статусом backend.
- FastAPI backend, environment config, подключение PostgreSQL/PostGIS.
- Compose с persistent volume, health checks и отдельной задачей миграции.
- Alembic, тесты, lint/typecheck, npm/Python locks, GitHub Actions workflow.
- README и документация архитектуры, разработки, данных, модулей, scoring.

## Изменённые файлы

`frontend/`, `backend/`, `docker-compose.yml`, `.env.example`, `.gitignore`,
`.github/workflows/checks.yml`, `README.md`, `CHANGELOG.md`, `docs/`;
README для `modules/`, `data/`, `infra/`, `scripts/`, `tests/`.
Исходный Master Specification сохранён без изменений.

## Миграции

`0001_postgis`: `CREATE EXTENSION IF NOT EXISTS postgis`.
Offline SQL сгенерирован успешно. Применение к реальному PostGIS не подтверждено:
Docker и сервер PostgreSQL в текущем окружении отсутствуют.

## API

- `GET /api/health/live`: 200, процесс работает.
- `GET /api/health/ready`: 200 при доступном PostGIS и актуальной миграции;
  иначе 503 без технических подробностей/секретов.
- `/docs`: OpenAPI UI.

## Проверки

- backend: PASS — Uvicorn запущен, реальный HTTP liveness 200.
- frontend: PASS — Vite запущен, HTTP 200; production build успешен.
- proxy: PASS — `/api/health/ready` через frontend возвращает ожидаемый 503 без БД.
- tests: PASS — backend 4, frontend 4; один PostGIS integration test SKIPPED.
- lint: PASS — Ruff и ESLint.
- typecheck: PASS — mypy и TypeScript.
- migration SQL: PASS — Alembic offline generation.
- npm audit при установке: 0 известных уязвимостей.
- UI: проверены снимки Firefox desktop 1280×800 и mobile 390×844;
  они подтверждают вёрстку начального состояния, но не весь интерактивный сценарий.
- Docker Compose / PostGIS integration: BLOCKED — Docker отсутствует.
- git diff проверен; diff --check чист для реализации. В исходном ТЗ сохранены
  четыре Markdown line breaks (trailing spaces).
- CI workflow добавлен, но удалённый запуск в рамках этой работы не выполнялся.

## Известные ограничения

Полная приёмка SPRINT 0 остаётся открытой до `docker compose up --build --wait`
и интеграционных проверок по docs/development.md в окружении с Docker.
Реальный успешный статус БД и применение миграций нельзя считать проверенными.
Карта и datasets ещё не реализованы; стек MapLibre/OSM/GeoJSON/PostGIS сохранён.

## Следующий рекомендуемый этап

Завершить Docker/PostGIS-приёмку SPRINT 0. После неё, только по команде владельца:
SPRINT 1 — Минимальная карта.
