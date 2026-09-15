# Changelog

## 0.1.0 — SPRINT 0

- React/TypeScript shell с реальной проверкой доступности API.
- FastAPI liveness/readiness, конфигурация БД, безопасные ошибки.
- Docker Compose, PostgreSQL/PostGIS, Alembic migration job.
- Unit/API tests, opt-in PostGIS integration test, lint/typecheck и dependency locks.
- Документация архитектуры, запуска и границ спринта.
- Исправлена гонка между временным PostgreSQL при первом init и Alembic job.
- Docker/PostGIS, миграция, HTTP proxy и persistent volume приняты на реальном стеке.
