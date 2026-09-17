# Changelog

## SPRINT 13

- Added a real bounded OSM roads import with structured KAD/ZSD corridors,
  primary/trunk/motorway roads, source-tagged ramps and interchanges.
- Added specialized road fields, PostGIS indexes, viewport API, independent
  map layers and straight-line road proximity queries.

## SPRINT 12

- Imported 5,248 named medical facilities from a dated Petersburg OSM snapshot,
  including clinics, hospitals, diagnostics, laboratories, dentistry and pharmacies.
- Added medical organizations, services, provenance, ownership confidence, spatial
  API and independent medical/pharmacy layers with viewport pharmacy clustering.

## SPRINT 11

- Added real public/private/unknown kindergarten import, specialized fields,
  provenance, bbox API, map layer/card and straight-line nearby analysis.
- Recorded official admissions rules as sourced text without invented polygons.

## SPRINT 10

- Added specialized school storage, broad OSM school import, source freshness and
  confidence, bbox API, school layer/card and explicit catchment uncertainty.

## SPRINT 9

- Added a real OSM sample of bus, tram and trolleybus routes with 441 distinct
  stops, stable IDs, directions, provenance and repeatable import.
- Added independent surface transport layers and nearby stop/route analysis.

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
## SPRINT 14

- Added separate road and railway spatial influence datasets over canonical PostGIS objects.
- Added explicit source type, confidence, date, method and null acoustic intensity.
- Added four independently controlled layers, viewport API, availability and point proximity.
- Documented missing aviation contours and helicopter routes without inferred geometry.
## SPRINT 15

- Added separate PostGIS user geometries and narrow CRUD API for Point, LineString and Polygon.
- Added drawing, vertex editing, cancel, save, reload and explicit delete controls.
- Added three Layer Registry entries and distinct dark-map styling without routing dependencies.
