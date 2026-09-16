# Модули

SPRINT 6 adds the `open_data` adapter. Its deliberately small base dataset has
18 current OSM district relations represented by provider-computed center points.
It exercises initial and repeatable imports without turning the repository into a
production OSM mirror. Domain modules reuse the same adapter/pipeline boundary.

SPRINT 5 добавляет общий ingestion CORE в `app/ingestion`. Он не содержит
предметных данных. Новый адаптер обязан выдать raw payload и нормализованный
`ImportRecord`, а pipeline выполняет staging, validation, idempotent upsert,
статистику и provenance.

SPRINT 4 adds application search over CORE objects and a replaceable geocoder
adapter. It does not add an ingestion, external POI, or domain data module.

SPRINT 3 добавляет canonical object persistence/API и категории в CORE.
Предметные модули и search/geocoding отсутствуют; поиск отложен до SPRINT 4
по отдельному указанию владельца. Районы не включаются в POI model.

SPRINT 0–2 реализуют инфраструктурный CORE: health/migrations, MapLibre shell,
application state районов и минимальный Layer Registry. Районы пока являются
core geographic selector на локальном development dataset, а не отдельным
предметным модулем или ingestion pipeline.

Предметные модули ещё не созданы. Порядок их реализации определяет Master
Specification, разделы 70–92. Категории, общие object filters, search, import,
routing и scoring не входят в SPRINT 2.
