# Changelog

## SPRINT 2

- Added all 18 Saint Petersburg district geometries from an OSM-derived local snapshot.
- Added synchronized district multi-selection, dimming, visibility, opacity, and deterministic layer ordering.
- Added accessible responsive controls and source/license documentation.

## 0.1.0 — SPRINT 0

- React/TypeScript shell с реальной проверкой доступности API.
- FastAPI liveness/readiness, конфигурация БД, безопасные ошибки.
- Docker Compose, PostgreSQL/PostGIS, Alembic migration job.
- Unit/API tests, opt-in PostGIS integration test, lint/typecheck и dependency locks.
- Документация архитектуры, запуска и границ спринта.
- Исправлена гонка между временным PostgreSQL при первом init и Alembic job.
- Docker/PostGIS, миграция, HTTP proxy и persistent volume приняты на реальном стеке.

## 0.2.0 — SPRINT 1

- Добавлена минимальная карта Санкт-Петербурга на MapLibre GL JS.
- Временная OpenFreeMap development-подложка вынесена в заменяемую конфигурацию.
- Добавлены один demo GeoJSON Point, выбор по stable ID и React-карточка.
- Добавлены lifecycle, error и responsive состояния карты и frontend tests.
