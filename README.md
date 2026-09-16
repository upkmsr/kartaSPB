# KARTASPB

Персональная GIS-система для Санкт-Петербурга и Ленинградской области.
Master Specification: [KARTASPB_AI_AGENT_SPEC.md](KARTASPB_AI_AGENT_SPEC.md).

## Текущий этап

SPRINT 13 — дорожная инфраструктура: 5 594 реальных OSM-объекта,
структурированные сегменты КАД и ЗСД, съезды, явно размеченные развязки,
bbox API и отдельные слои. После запуска выполните
`docker compose exec backend python -m app.roads`. Дороги загружаются картой
по текущей области; расстояния в API вычисляются по прямой, без routing.

SPRINT 12 — медицинская инфраструктура Петербурга: 5 248 физических объектов
из снимка OSM, отдельная медицинская модель, услуги и организации, bbox API,
слои клиник и аптек. После запуска выполните
`docker compose exec backend python -m app.medical`. Аптеки загружаются по
текущей области карты и группируются MapLibre. Значение `unknown` означает,
что тип собственности не подтверждён источником.

SPRINT 11 — детские сады Петербурга: отдельная модель/API, слой и фильтры
государственных/частных садов. После запуска выполните
`docker compose exec backend python -m app.kindergartens`.

SPRINT 10 — школы Петербурга: 1 031 объект из OSM, отдельная модель и bbox API,
слой школ и явное предупреждение об отсутствии проверенных полигонов закрепления.
После запуска выполните `docker compose exec backend python -m app.schools`.

SPRINT 5–9 — общий ingestion pipeline и реальные, ограниченные снимки OSM:
базовые районы, природа/вода, метро и наземный транспорт. Импорт выполняется
явными командами после запуска Compose; на чистой БД предметные таблицы пусты:

```bash
docker compose exec backend python -m app.open_data
docker compose exec backend python -m app.nature
docker compose exec backend python -m app.metro
docker compose exec backend python -m app.transport
```

Повторный import обновляет объекты без дублей. Источники, лицензии, охват и
ограничения: [docs/data-sources.md](docs/data-sources.md).

SPRINT 4 — раздельный поиск объектов KARTASPB и адресов/мест. Введите не менее
двух символов; результаты проекта открывают canonical Object Card, географические
результаты перемещают карту и показывают временный маркер.

SPRINT 3 — canonical project objects, категории и локальные category filters.
Объекты загружаются из PostgreSQL/PostGIS через read-only API.
На чистой БД список объектов пуст; для демонстрации после запуска выполните:

```bash
docker compose exec backend python -m app.seed_demo
```

Команда добавляет исходный `demo-object-1` идемпотентно. Перезагрузите страницу.
Категории «Демонстрационные» и «Прочее» создаются миграцией.

SPRINT 0 — Repository & Architecture завершён и принят в Docker/PostGIS.
SPRINT 1 — минимальная карта Санкт-Петербурга на MapLibre GL JS завершён.
SPRINT 2 — 18 районов, multi-select, визуальное выделение и Layer Registry:
выбирайте районы в панели или кликом по полигону, настраивайте видимость и
прозрачность районов и demo-объекта.
Стек карты: MapLibre GL JS + OSM/open geodata + GeoJSON/PostGIS.
Демонстрационная точка не является реальным городским объектом и не сохраняется в БД.

## Запуск

Нужен Docker с Compose v2. Из корня репозитория:

```bash
docker compose up --build --wait
```

Команда использует локальные значения по умолчанию, поэтому копировать
`.env.example` для первого запуска не требуется. Для собственной конфигурации
скопируйте его в `.env` и измените значения. Первый запуск требует интернета для
загрузки образов и зависимостей.
Бесплатная development-подложка OpenFreeMap требует интернета для
стиля и тайлов. Конфигурация источника: `frontend/src/config/map.ts`;
условия и attribution: [источники данных](docs/data-sources.md).

- Интерфейс: http://localhost:5173
- API docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/api/health/live
- Readiness (PostGIS и миграция): http://localhost:8000/api/health/ready
- Project Search: `GET /api/search/objects?q=Тестовый`
- Geographic Search: `GET /api/search/geocode?q=Дворцовая площадь`
- Import runs: `GET /api/import/runs`
- Nearest metro: `GET /api/analysis/metro/nearest?lon=30.3158&lat=59.9391`
- Nearby transport: `GET /api/analysis/transport/nearby?lon=30.3158&lat=59.9391`
- Schools: `GET /api/schools?bbox=30.2,59.8,30.4,60.0`
- School catchment status: `GET /api/schools/catchments`
- Kindergartens: `GET /api/kindergartens?bbox=30.2,59.8,30.4,60.0`
- Nearby kindergartens: `GET /api/kindergartens/nearby?lon=30.3158&lat=59.9391`
- Medical: `GET /api/medical?bbox=30.2,59.8,30.4,60.0&type=hospital`
- Pharmacies: `GET /api/medical/pharmacies.geojson?bbox=30.2,59.8,30.4,60.0`
- Roads: `GET /api/roads?bbox=30.2,59.8,30.4,60.0&corridor=kad`
- Road viewport: `GET /api/roads/viewport.geojson?bbox=30.2,59.8,30.4,60.0`
- Nearest roads: `GET /api/analysis/roads/nearest?lon=30.3158&lat=59.9391`

Compose ждёт БД, выполняет `alembic upgrade head`, затем запускает API и frontend.
БД хранится в named volume, порт БД наружу не публикуется.
Остановка: `docker compose down` (данные сохраняются).
Пароль по умолчанию предназначен только для локальной разработки.

## Проверки

```bash
docker compose run --rm backend pytest
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -m integration
docker compose run --rm backend ruff check .
docker compose run --rm backend ruff format --check .
docker compose run --rm backend mypy app
cd frontend
npm ci
npm test
npm run lint
npm run typecheck
npm run build
```

См. [разработка](docs/development.md), [архитектура](docs/architecture.md),
[отчёты по спринтам](docs/README.md), [изменения](CHANGELOG.md).
