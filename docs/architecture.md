# Архитектура

## SPRINT 12 — Medical

`app.medical` reuses the canonical ingestion pipeline, source registry, staging,
validation, stable OSM IDs and provenance. `medical_facilities` stores medical
fields separately from `project_objects`; `medical_services` stores tagged
specializations, and `medical_organizations` groups only source-provided brands
or operators. Each mapped OSM facility remains a separate point, even when it
belongs to a network. Ownership is `public`, `private` or `unknown`; absent
operator evidence is never inferred from a clinic name.

`/api/medical` supports indexed bbox, subtype, ownership and 24h filters with
limit/offset pagination.
Pharmacies are excluded from the initial canonical-object response used by React.
MapLibre requests `/api/medical/pharmacies.geojson` for the current viewport,
clusters the points and fetches individual Object Cards by canonical ID. Two
Layer Registry entries control medical facilities and pharmacies independently.

## SPRINT 11 — Kindergartens

`app.kindergartens` uses the same ingestion pipeline and shared `app.education`
field-normalization helpers as Schools. It has its own specialized table and API,
while canonical point geometry and source provenance remain in CORE. Public,
private and unknown are separate canonical categories, so existing category
filters provide type selection; one Layer Registry entry controls kindergarten
visibility. `/api/kindergartens` accepts bbox/limit, and `/nearby` returns
straight-line PostGIS distance plus nearby public/private/unknown counts.
Admission rules are stored as source-linked text, never synthesized geometry.

## SPRINT 10 — Schools

`app.schools` reuses the source/staging/validation/provenance pipeline, with an
atomic `after_upsert` callback for specialized `schools` rows. Canonical geometry
stays in `project_objects`; specialized admissions/capacity fields stay in
`schools` and are NULL unless supported. `/api/schools` accepts a bbox and limit;
the existing GiST geometry index supports viewport filtering. The map layer uses
canonical objects and existing Layer Registry. `school_catchments` supports future
verified MultiPolygons with a GiST index but currently contains only source-level
`address_list` metadata, so the independent catchment layer is empty by design.

## SPRINT 9 — Surface Transport

`app.transport` keeps route MultiLineStrings and stop Points as different
canonical entities. Route properties retain type, ref and direction; stop
properties retain arrays of served route types/refs and unique route IDs. The Layer Registry exposes
bus, tram, trolleybus and stops independently. MapLibre renders the GeoJSON source
directly; React creates no per-route DOM nodes. The current 450-object bounded
sample fits one API response. `/api/analysis/transport/nearby` uses indexed
PostGIS distance to report nearby stop/route counts and up to ten nearest stops.

## SPRINT 8 — Metro

The isolated `app.metro` module imports line MultiLineStrings and station/entrance
Points into canonical objects. Three Layer Registry entries control their MapLibre
rendering independently; line color comes from normalized source properties.
Clicks use the shared ID-to-Object-Card path. `/api/analysis/metro/nearest` uses
PostGIS geography distance and labels its method `straight-line`; routing is not
simulated.

## SPRINT 7 — Nature

The isolated `app.nature` importer classifies source tags into canonical
`nature-green` and `nature-water` categories. Closed OSM ways remain polygons and
open waterways/embankments remain lines. MapLibre renders fill and line sublayers
from the shared canonical GeoJSON source; registry visibility/opacity and category
filters are independent. A rendered feature click resolves its canonical ID into
the existing React Object Card, including source attribution.

## SPRINT 6 — Base OSM/Open Geodata

`app.open_data.overpass` is a bounded source adapter, separate from the basemap.
It reads a local raw snapshot for deterministic initial/repeat imports and can
explicitly refresh that snapshot query from Overpass. Provider element type/ID is
the identity; the shared pipeline stores raw payload, validates geometry, upserts
canonical objects and records statistics/provenance. Normal application runtime
reads PostGIS only.

## SPRINT 5 — Data Ingestion Framework

Любой внешний dataset проходит одинаковую границу: source adapter → immutable raw
staging → normalization → validation → deterministic upsert в canonical objects →
provenance. `data_sources` хранит лицензию и attribution, `ingestion_runs` — реальные
счётчики запуска, `ingestion_errors` — диагностируемые ошибки, а
`object_provenance` связывает canonical object с исходной записью и временем проверки.

Импорты запускаются CLI/worker-командами и не удерживают HTTP request. Read-only
эндпоинты `/api/import/status`, `/api/import/runs` и `/api/import/errors` дают
операционную видимость. Стабильный canonical ID строится из source ID и source record
ID; повторный импорт делает upsert и обновляет provenance без создания объектов.

## SPRINT 4 — Search & Geocoding

Project Search and geographic search are separate endpoints and repositories.
`/api/search/objects` queries canonical `project_objects`; it has no dependency on
Nominatim, OpenFreeMap or the tile provider. `GeocoderProvider` returns normalized
`GeocodingResult` values and currently talks to the backend Nominatim proxy.

React owns the current query/results and reuses `selectedObject`. Project result
selection opens the existing card and calls the map adapter `focus`; geographic
selection clears the card and replaces GeoJSON in the temporary `search-result`
source. Neither operation recreates MapLibre or writes to PostGIS.

## SPRINT 3 — текущая object pipeline

`project_objects` (PostGIS) → `app/objects.py` repository/read-only API →
`data/objectsApi.ts` → canonical `MapObject[]` → `toGeoJSON()` → MapLibre source.
Domain object содержит id, name, categoryId, description, geometry, properties,
optional source/sourceId. Геометрия не зависит от MapLibre; БД поддерживает Point,
LineString, Polygon и Multi-эквиваленты в EPSG:4326. Текущий object renderer — circles
для Point; рендер линий/полигонов добавляется вместе с использующими их модулями.

Категории хранятся в `categories` с FK из объектов: стабильный id, display name,
description, color и defaultVisible. Единственный registry — ответ categories API;
карточка получает display name через getCategoryById. React хранит объекты,
selectedObject и visibleCategoryIds. Пустой visibleCategoryIds скрывает все объекты;
«Показать все» восстанавливает все категории. Checkbox не вызывает запрос API.
Backend отдельно поддерживает `?category=demo,other`; неизвестный/пустой набор
возвращает пустой список. DTO — JSON array, geometry — GeoJSON-compatible.

Существующий Layer Registry сохранён: ключ `demo-object` теперь управляет всеми
объектами проекта (display name «Объекты проекта»). Районы остаются отдельной
сущностью и source. Ошибка object API не меняет состояние районов и basemap.

Production worker MapLibre включается через Vite `?worker&url` и `setWorkerUrl`,
согласно [официальной инструкции](https://maplibre.org/maplibre-gl-js/docs/).
Это исправляет обнаруженную при реальном QA незагружавшуюся worker-программу.
OpenFreeMap остаётся тем же provider; TileJSON `/planet` задаёт актуальный tile URL.

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

## SPRINT 1 — Минимальная карта

- `frontend/src/config/map.ts`: начальный viewport, same-origin URL style JSON и attribution.
  Минимальный dark style находится в `frontend/public/basemap/`, а внешний vector
  source остаётся заменяемым через style config.
  Источник можно заменить на другой MapLibre-совместимый, в том числе same-origin
  self-hosted style, изменив конфигурацию и пересобрав frontend.
- `frontend/src/domain/mapObject.ts`: GeoJSON-based `MapObject`, `ObjectProperties`,
  `SelectedObject`; типы предметной области не зависят от MapLibre.
- `frontend/src/data/demo/point.json`: ровно один fixture с устойчивым ID.
- `frontend/src/map/mapLibreAdapter.ts`: MapLibre instance, viewport, controls,
  GeoJSON source, circle layer, map events. Клик передаёт только ID.
- `frontend/src/components/MapView.tsx`: DOM container, lifecycle, ResizeObserver,
  сообщения загрузки/ошибки. Unmount вызывает `map.remove()`; обычный rerender,
  смена callback и открытие/закрытие карточки не пересоздают карту.
- `App.tsx`: определяет объект по ID из собственного demo dataset и хранит
  `selectedObject`. Свойства из map event не становятся содержимым карточки.
- `ObjectCard.tsx`: отдельная React-карточка. Закрытие сбрасывает `selectedObject`
  в `null`. На mobile высота ограничена, содержимое прокручивается; attribution
  и навигационные controls остаются доступными.

Basemap и demo source разделены. Клик не делает API/геокодирование или запрос БД.
Внешняя подложка разрешена текущей командой владельца как временное development
решение; полноценный offline runtime пока не реализован. Backend и миграции
спринта 0 не изменены. CORE + MODULES сохраняется; следующие модули не создаются.

## SPRINT 2 — Районы и слои

- `frontend/src/data/districts/` содержит локальный GeoJSON-снимок 18 районов.
  UI зависит от типизированного `District[]`, поэтому статический адаптер можно
  позже заменить узким API/PostGIS-репозиторием без изменения компонентов.
- `App.tsx` хранит `selectedDistrictIds` и `LayerRegistry` как единственные
  источники application state. MapLibre получает ID и передаёт клики обратно;
  собственное несинхронизированное состояние выбора в карте не создаётся.
- `domain/layers.ts` задаёт стабильные `districts` и `demo-object`, их visibility,
  opacity и order. Реестр обновляется чистыми функциями и не зависит от DOM.
- Map adapter создаёт отдельные GeoJSON sources и слои `district-fill`,
  `district-outline`, `demo-points`, `district-selected`. Порядок описан в одном
  месте. Выбор обновляет filter/paint, а visibility и opacity — layout/paint;
  MapLibre instance при этих действиях не пересоздаётся.
- При пустом выборе используется нейтральная заливка. При выборе MapLibre
  expression сохраняет выбранные полигоны светлыми и затемняет остальные.
