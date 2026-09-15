# Разработка

## Окружение

Целевое окружение: Docker Compose v2, Python 3.12, Node.js 24.
Backend также проверен на имеющемся Python 3.9.6; для новой установки используйте 3.12.

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

`0001_postgis` выполняет `CREATE EXTENSION IF NOT EXISTS postgis`.
Образ PostGIS может уже содержать расширение. Повторный upgrade безопасен.
Downgrade убирает запись Alembic, но намеренно сохраняет расширение: оно могло
существовать до приложения и использоваться другими пространственными таблицами.

Проверить в Compose:

```bash
docker compose run --rm migrate
docker compose run --rm migrate
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_Version();"'
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -m integration
```

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
