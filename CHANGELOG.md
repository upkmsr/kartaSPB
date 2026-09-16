# Changelog

## SPRINT 8

- Added real OSM metro lines, stations and entrances with stable IDs, provenance,
  source line colors and interchange metadata.
- Added independent metro layers and straight-line nearest-station analysis.

## SPRINT 7

- Added a real bounded OSM nature snapshot/importer with green and water
  categories, valid polygon/line geometry and provenance.
- Added independent green/water MapLibre layers, filters and Object Card source.

## SPRINT 6

- Added a bounded Overpass/OpenStreetMap adapter and a real 18-record Petersburg
  district snapshot with deterministic offline and refresh imports.
- Registered ODbL metadata and verified repeat imports, geometry and provenance.

## SPRINT 5

- Added the shared source registry, ingestion runs, staging, validation,
  normalization, deduplication keys, error records and object provenance.
- Added an idempotent transactional importer, acceptance fixture and import
  observability API.

## SPRINT 4

- Added bounded PostGIS project search over canonical objects and categories.
- Added replaceable, normalized Nominatim proxy with identification, throttling and cache.
- Added debounced accessible search UI, independent result sections, cancellation and stale protection.
- Added map focus and a non-persistent geographic result marker.

## SPRINT 3

- Canonical objects in PostGIS, category persistence, read-only API and category queries.
- Frontend API repository, category filters, canonical object card and empty/error states.
- Explicit idempotent development seed preserving demo-object-1.
- Fixed missing MapLibre production worker and preserved string IDs through properties.
- Restored provider TileJSON discovery; MapLibre/OpenFreeMap stack unchanged.

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
