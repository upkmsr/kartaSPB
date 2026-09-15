# Архитектура

## SPRINT 0

- `frontend/`: React + TypeScript + Vite; UI shell и отдельный API client.
- `backend/app/`: FastAPI, конфигурация из environment, подключение SQLAlchemy/psycopg.
- `backend/migrations/`: Alembic, расширение PostGIS без предметных таблиц.
- `modules/`: место для будущих модулей; бизнес-модули пока не созданы.
- `docker-compose.yml`: PostGIS → migration job → API → nginx/frontend.
- `/api` проксируется через nginx (Compose) или Vite (локальная разработка).
  URL backend не зашит в React; браузер использует один origin.

Healthcheck БД ждёт финальный PostgreSQL-процесс после первичной инициализации
образа; это исключает запуск миграции во время промежуточного рестарта сервера.
Liveness не зависит от БД. Readiness возвращает 503 при недоступности PostGIS
или несовпадении версии миграции. При новых миграциях обновлять ожидаемую ревизию.
Запросы синхронные: FastAPI выполняет их в thread pool.
Ошибки подключения не раскрывают credentials в ответах или журналах.

## Границы этапа

MapLibre GL JS остаётся выбранным движком для SPRINT 1.
Поставщик тайлов ещё не выбран, внешних API и геоданных нет.
Дальнейшие UI, application logic, map adapter и providers будут разделены.
CORE + MODULES сохраняется; преждевременных моделей и пустых реализаций модулей нет.
