# Разработка

## Окружение

Целевое окружение: Docker Compose v2, Python 3.12, Node.js 24.
Локальный backend требует Python 3.10+ (аннотации типов `|`); рекомендуемая
версия — 3.12, как в Docker-образе. Системный Python 3.9 не подходит.

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Без БД liveness работает, readiness корректно возвращает 503.
Для реальной БД задайте `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
в окружении backend. `.env` в корне читает Compose; локальный Python автоматически
его не загружает. Затем выполните `.venv/bin/alembic upgrade head`.

В другом терминале:

```bash
cd frontend
npm ci
npm run dev
```

Проверки backend: `.venv/bin/pytest`, `.venv/bin/ruff check .`,
`.venv/bin/ruff format --check .`, `.venv/bin/mypy app`.
Интеграционный тест требует реального PostGIS: `RUN_DB_TESTS=1 .venv/bin/pytest -m integration`.
Без этой переменной он явно пропускается.

## Миграции

Текущий head: `0009_kindergartens`, поверх `0001_postgis` → `0002_objects` →
`0003_ingestion` → `0004_open_data` → `0005_nature` → `0006_metro` →
`0007_transport` → `0008_schools`.
Создаёт categories, project_objects, ingestion tables и предметные категории;
geometry(Geometry,4326) имеет GiST spatial index.
Downgrade до 0001 удаляет новые таблицы вместе с их данными; применять только
к одноразовой тестовой БД или после backup. Обычный запуск выполняет только upgrade.

Development fixture: `docker compose exec backend python -m app.seed_demo`.
Повторный запуск не изменяет существующий объект. Production-схема не содержит
автоматического seed тестовых объектов.

Импорт предметных snapshots запускается отдельно и повторяемо:

```bash
docker compose exec backend python -m app.open_data
docker compose exec backend python -m app.nature
docker compose exec backend python -m app.metro
docker compose exec backend python -m app.transport
docker compose exec backend python -m app.schools
docker compose exec backend python -m app.kindergartens
```

`python -m app.open_data --refresh` выполняет новый ограниченный Overpass-запрос;
остальные команды используют зафиксированные raw snapshots для воспроизводимости.
`/api/import/status`, `/api/import/runs`, `/api/import/errors` показывают ход и
результаты. Source registry и provenance хранятся в PostGIS.

API smoke (через frontend proxy):

```bash
curl --fail http://localhost:5173/api/categories
curl --fail http://localhost:5173/api/objects
curl --fail 'http://localhost:5173/api/objects?category=demo,other'
curl --fail http://localhost:5173/api/objects/demo-object-1
```

Последняя команда требует выполненного development seed. Unknown ID → 404.

`0001_postgis` выполняет `CREATE EXTENSION IF NOT EXISTS postgis`.
Образ PostGIS может уже содержать расширение. Повторный upgrade безопасен.
Downgrade убирает запись Alembic, но намеренно сохраняет расширение: оно могло
существовать до приложения и использоваться другими пространственными таблицами.

Проверить в Compose:

```bash
docker compose up --build --wait
docker compose ps
docker compose run --rm migrate
docker compose run --rm migrate
docker compose exec backend alembic current
docker compose exec backend alembic heads
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_Version();"'
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -m integration
```

`migrate` — одноразовый обязательный сервис: после успешного выполнения его
нормальное состояние в `docker compose ps -a` — `Exited (0)`. Остальные сервисы
(`db`, `backend`, `frontend`) должны быть `healthy`.

## Roads import (SPRINT 13)

After `docker compose up --build --wait`, run
`docker compose exec backend python -m app.roads`. The checked-in bounded OSM
snapshot is imported idempotently. The map requests selected road categories
for the current viewport from `/api/roads/viewport.geojson`; the analysis API
reports straight-line distances and does not perform routing.

## Medical import (SPRINT 12)

After `docker compose up --build --wait`, run
`docker compose exec backend python -m app.medical`. This imports the checked-in
OSM snapshot into canonical objects and the specialized medical tables. Running
it again updates existing OSM IDs. Inspect with
`docker compose exec backend alembic current`,
`GET /api/medical?bbox=30.2,59.8,30.4,60.0` and
`GET /api/medical/pharmacies.geojson?bbox=30.2,59.8,30.4,60.0`.
The pharmacy endpoint requires bbox and caps results at 3,000; the map loads
only the visible area when its pharmacy layer is enabled.

## Зависимости

`package-lock.json` фиксирует npm дерево. `requirements.lock` фиксирует Python
зависимости разработки и runtime; образ этого спринта включает инструменты проверок.
`requirements*.txt` задают допустимые диапазоны для осознанного обновления lock.
После обновлений проверять лицензии, security advisories, совместимость, сборку и тесты.
Ни одна зависимость не требует платного API.

React/Vite/TypeScript и FastAPI/SQLAlchemy/Alembic нужны для указанного в ТЗ стека;
psycopg — PostgreSQL driver, pydantic-settings — env validation.
GIS processing библиотеки пока не добавляются. Основные лицензии: MIT (React,
Vite, FastAPI, SQLAlchemy, Alembic), Apache-2.0 (TypeScript), LGPL-3.0 (psycopg),
PostgreSQL License (PostgreSQL), GPL-2.0-or-later (PostGIS).

Основания выбора инфраструктуры:
[Vite requirements](https://vite.dev/guide/),
[FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/),
[PostGIS image](https://hub.docker.com/r/postgis/postgis/).

## UI QA

На desktop и mobile проверить отсутствие горизонтальной прокрутки, читаемость,
состояния загрузки/готовности/ошибки и кнопку повторной проверки.
Без подключения к БД не выдавать статус «Система готова».

Образ PostGIS запускается как linux/amd64; на Apple Silicon нужна поддержка
эмуляции Docker. CI проверяет весь Compose на Ubuntu, включая повторный upgrade.

## Проверки SPRINT 1

`npm test` включает React tests в jsdom: mock только MapLibre/WebGL boundary,
настоящие adapter, выбор по ID, `selectedObject`, карточка и close проверяются
вместе. Проверяется также StrictMode cleanup, смена callback без пересоздания
карты, неизвестный ID и сообщение о сбое basemap.

В реальном браузере после `docker compose up --build --wait`:

1. Открыть `http://localhost:5173/` на 1280×800 и 390×844 с WebGL и интернетом.
2. Дождаться улиц/воды Петербурга, мятной точки и attribution источников.
3. Выполнить development seed, обновить страницу, нажать точку: видны название,
   «Демонстрационные», описание, `demo-object-1`.
4. Закрыть карточку кнопкой ×; повторить выбор. Начальный viewport сохраняется.
5. На mobile проверить touch, отсутствие горизонтального overflow, доступность
   controls и attribution, прокрутку содержимого карточки при необходимости.
6. После загрузки отключить сеть: выбор и закрытие карточки продолжают работать.

Браузерный QA проверяет настоящий WebGL, а не unit mock. Playwright и временные
снимки для разовой проверки не являются зависимостями или artifacts репозитория.
