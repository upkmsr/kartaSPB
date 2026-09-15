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
Применена к реальному PostgreSQL 17/PostGIS 3.5. `alembic current` и
`alembic heads` возвращают `0001_postgis (head)`.

## API

- `GET /api/health/live`: 200, процесс работает.
- `GET /api/health/ready`: 200 при доступном PostGIS и актуальной миграции;
  иначе 503 без технических подробностей/секретов.
- `/docs`: OpenAPI UI.

## Проверки

- Docker Compose: PASS — чистый `docker compose up --build --wait`.
- PostgreSQL/PostGIS: PASS — контейнер healthy, `PostGIS_Version()` = 3.5.
- backend: PASS — контейнер healthy; live и ready возвращают HTTP 200.
- frontend: PASS — контейнер healthy, HTTP 200, proxy readiness HTTP 200.
- persistent volume: PASS — маркер сохранился после `docker compose down` и повторного запуска.
- tests: PASS — backend 5 (включая PostGIS integration), frontend 4, без skip.
- lint: PASS — Ruff и ESLint.
- typecheck: PASS — mypy и TypeScript.
- migration: PASS — Alembic current совпадает с head; повторный upgrade успешен.
- npm audit при установке: 0 известных уязвимостей.
- UI: проверены снимки Firefox desktop 1280×800 и mobile 390×844;
  они подтверждают вёрстку начального состояния, но не весь интерактивный сценарий.
- git diff проверен; diff --check чист для реализации. В исходном ТЗ сохранены
  четыре Markdown line breaks (trailing spaces).
- CI workflow добавлен; его проверки воспроизведены локально.

## Известные ограничения

Одноразовый сервис `migrate` после успеха имеет ожидаемый статус `Exited (0)`;
постоянные сервисы `db`, `backend`, `frontend` имеют статус healthy.
Карта и datasets ещё не реализованы; стек MapLibre/OSM/GeoJSON/PostGIS сохранён.

## Следующий рекомендуемый этап

Только по отдельной команде владельца: SPRINT 1 — Минимальная карта.
