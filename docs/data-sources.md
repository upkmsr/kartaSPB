# Источники данных

## SPRINT 11 — Kindergartens

- Source: OpenStreetMap `amenity=kindergarten` nodes, ways and relations within
  OSM Petersburg area `3600337422`, collected 2026-09-16 through
  `https://overpass-api.de/api/interpreter`. License ODbL 1.0; attribution
  © OpenStreetMap contributors. Raw snapshot:
  `backend/app/kindergartens/snapshots/spb_kindergartens.json`.
- Source returned 1,575 elements; 1,503 named objects are eligible for initial
  import. Provider-computed centers represent way/relation locations, not entrances.
  OSM type/ID is retained, so distinct buildings are not merged solely by name,
  ref or nearby coordinates.
- Public/private uses only explicit `operator:type`; missing/other values remain
  `unknown`. Confidence is the documented completeness score used for Schools,
  not a quality or availability rating. Source snapshot time and optional
  `check_date` are separate fields; capacity/price/reviews remain NULL.
- Official admissions source: [Saint Petersburg government admission page](https://www.gov.spb.ru/gov/terr/reg_center/obrazovanie/poryadok-priema-v-obrazovatelnye-uchrezhdeniya/)
  describes 2026 kindergarten placement periods and rules. Saved as `text_rule`
  with source URL; it is not converted into a polygon or an admission guarantee.
- Limitations: OSM has incomplete private-kindergarten tagging and does not
  provide a complete official registry or live availability. No fees are inferred.

## SPRINT 10 — Schools

- Source: OpenStreetMap `amenity=school` nodes, ways and relations within OSM
  Petersburg area `3600337422`, collected 2026-09-16 from
  `https://overpass-api.de/api/interpreter`. License ODbL 1.0; attribution
  © OpenStreetMap contributors. Raw snapshot:
  `backend/app/schools/snapshots/spb_schools.json`.
- The source returned 1,061 elements, of which 1,031 have names and are eligible
  for initial import. OSM element type/ID is the stable campus/building identity;
  distinct mapped buildings are not merged on school number alone.
- Location for ways/relations is the Overpass-computed center, not an invented
  entrance. Type uses explicit tags or name keywords. Public/private uses only
  `operator:type`; otherwise `unknown`. `ref` is kept as source-provided school
  number, not asserted to be a globally unique official registry ID.
- Confidence is a transparent completeness score: base 0.5 plus 0.1 each for
  address, website, source `ref`, and operator type. It is not an admission or
  educational-quality rating. OSM base timestamp and optional per-element
  `check_date` are exposed separately.
- Official catchment research: the [Saint Petersburg government admission page](https://www.gov.spb.ru/gov/terr/reg_center/obrazovanie/poryadok-priema-v-obrazovatelnye-uchrezhdeniya/)
  links district decrees and address lists. No verified polygon dataset was found
  for this import. The catchments API records `address_list` and explains that
  a point lookup cannot guarantee admission. No polygon is synthesized.
- Limitations: OSM coverage and private-school tagging are incomplete; specialized
  outcome/capacity/rating fields remain NULL. This is not the official education
  registry and should be cross-checked before decisions.

## SPRINT 9 — Surface transport sample

- Source: OpenStreetMap through Overpass; ODbL 1.0,
  © OpenStreetMap contributors.
- Collection: 2026-09-16. A metadata query over central Petersburg selected the
  lowest stable relation IDs for three bus, three tram and three trolleybus route
  relations. The checked-in bounded snapshot contains those route geometries and
  their tagged member stops: `backend/app/transport/snapshots/spb_transport.json`.
- Dataset: 9 directed route entities and 441 distinct stop entities. Stable IDs
  are `osm-transport-relation-<id>` and `osm-transport-node-<id>`. Direction,
  route type/ref and stop-to-route membership come from OSM tags/members.
- Known limitation: this is a deterministic, representative sample, not the full
  Petersburg network or schedule. OSM membership may be incomplete. Nearby
  analysis uses straight-line PostGIS geography distance; it is not travel time.
  A larger refresh should run as regional extract processing and viewport APIs.

## SPRINT 8 — Saint Petersburg metro

- Source: OpenStreetMap through bounded Overpass query; ODbL 1.0,
  © OpenStreetMap contributors.
- Collection: 2026-09-16 inside OSM Petersburg area `3600337422`: subway route
  relations, `railway=station + station=subway` nodes and
  `railway=subway_entrance` nodes. Raw snapshot:
  `backend/app/metro/snapshots/spb_metro.json`.
- Method: opposite route directions share `ref`; one relation per ref supplies six
  displayed line geometries. Station membership in route relations becomes
  `lineRefs`; multiple refs mark an interchange where source membership supports
  it. Provider colors are mapped to official line display colors.
- Snapshot yields 6 lines, 72 stations and 261 entrances. Stable IDs retain the
  OSM type and ID. Known limitation: entrances without a source name use the
  generic descriptive label “Вход в метро”; route membership in OSM can be
  incomplete. Nearest-station distance is geodesic straight-line distance and is
  explicitly returned as `method=straight-line`, not walking time.

## SPRINT 7 — Nature snapshot

- Source: named OpenStreetMap ways through the same Overpass endpoint; ODbL 1.0,
  © OpenStreetMap contributors.
- Collection: 2026-09-16, bbox `59.75,29.65,60.15,30.65`; named parks, gardens,
  forests/woods, grass/recreation areas, natural water, rivers, canals and mapped
  embankments. Raw snapshot is `backend/app/nature/snapshots/spb_nature.json`.
- Method: provider way geometry becomes Polygon when closed and LineString
  otherwise. Stable IDs are `osm-nature-way-<id>`; original tags are retained in
  staging and classification/OSM IDs in canonical properties.
- Known limitations: only named OSM ways in the bounded snapshot are included;
  unnamed areas, multipolygon relations and a complete analytical polygon for the
  Gulf of Finland are not represented in this first controlled dataset. Coverage
  and naming reflect OSM, not an official inventory.

## SPRINT 6 — bounded OpenStreetMap import

- Source: OpenStreetMap through `https://overpass-api.de/api/interpreter`.
- License: ODbL 1.0; attribution: © OpenStreetMap contributors.
- Collection: bounded Overpass QL query inside OSM area `3600337422`
  (Санкт-Петербург), limited to `boundary=administrative`, `admin_level=5`.
- Snapshot: `backend/app/open_data/snapshots/spb_district_centers.json`, collected
  2026-09-16. It contains 18 relation records and provider metadata. The importer
  uses real relation IDs and provider-computed centers; it does not manufacture
  coordinates.
- Refresh: `python -m app.open_data --refresh` performs the same bounded query;
  `python -m app.open_data` repeats the checked-in snapshot offline. Both use the
  SPRINT 5 pipeline and deterministic `osm-overpass-relation-<id>` IDs.
- Known limitation: the SPRINT 6 dataset intentionally stores district centers,
  not complete OSM geometry or the planet extract. The public Overpass instance
  has usage limits and no SLA. Larger production imports should use a regional
  PBF extract (for example Geofabrik) and local processing.

This dataset is separate from OpenFreeMap vector tiles and is never requested by
MapLibre during pan or zoom.

## Source registry (SPRINT 5)

Внешний источник допускается в importer только после регистрации URL, лицензии,
attribution, типа, приоритета и ограничений в `data_sources`. Raw записи сохраняются
в staging до validation. `test-fixture` и `integration-fixture` — явно синтетические
локальные fixtures для проверки pipeline; они не являются геоданными продукта.

## SPRINT 4 — Nominatim development geocoder

- Endpoint by default: `https://nominatim.openstreetmap.org/search`; configurable
  with `GEOCODER_URL` without rebuilding the frontend.
- Identification: configurable `GEOCODER_USER_AGENT`; requests run through backend.
- Policy checked 2026-09-16: absolute maximum 1 request/second, valid identifying
  User-Agent/Referer, visible attribution, provider replaceability and caching.
- Implementation serializes requests, enforces at least one second between uncached
  calls, caches identical query/limit pairs in process, limits results to 10, and
  only sends searches explicitly submitted by the user. It does not implement
  Nominatim autocomplete; debounce applies only to independent project search.
- Public Nominatim forbids client-side autocomplete, bulk/systematic requests,
  POI downloads and confidential/personal query data. This integration is for
  moderate development use; production or higher traffic requires a separately
  selected/self-hosted provider.
- Results: © OpenStreetMap contributors, ODbL. Attribution is shown in results and
  the map. Results are temporary and are not inserted into project objects.

Policy: https://operations.osmfoundation.org/policies/nominatim/

## SPRINT 1 — development basemap

Проверено 2026-09-15:

- Provider: [OpenFreeMap](https://openfreemap.org/), публичный бесплатный instance.
- Style: same-origin `/basemap/openfreemap-dark.json`, MapLibre Style Specification
  v8, with a replaceable OpenFreeMap vector source. The local style avoids making
  project-layer initialization depend on remote sprites, glyphs or style JSON.
- Vector TileJSON: `https://tiles.openfreemap.org/planet` в локальном style JSON.
  Актуальный versioned tile template берётся из ответа provider.
- Данные: OpenStreetMap, схема OpenMapTiles; на малых zoom также Natural Earth.
- Attribution: OpenFreeMap · © OpenMapTiles · Data from OpenStreetMap.
  MapLibre AttributionControl показывает её полностью, включая на mobile;
  дополнительные attribution из style sources сохраняются.
- OpenFreeMap code: MIT; OSM data: ODbL; OpenMapTiles schema: BSD-3-Clause,
  cartography: CC-BY 4.0. Компонентные лицензии: [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).
- Provider не требует регистрации, токенов или оплаты; заявляет отсутствие
  лимитов на views/requests и разрешает коммерческое использование.
  SLA отсутствует, доступность и неизменность условий не гарантируются.
- [Условия](https://openfreemap.org/tos/) и [quick start](https://openfreemap.org/quick_start/).
  Использовать для обычного отображения карты, без массового scraping/prefetch.
  Для self-hosting использовать документированные provider downloads.
- Provider сообщает о еженедельных planet downloads. Свежесть конкретных
  городских объектов приложением не проверена; карта не используется как аналитический dataset.

URL, attribution, center и zoom находятся в `frontend/src/config/map.ts`.
Для смены источника изменить `style.url` и `style.attribution`, затем пересобрать
frontend (`docker compose up --build --wait` или `npm run build`). React UI
и обработчик выбора объекта при этом не меняются. Для локальной карты URL может
быть `/basemap/style.json`, но этот style должен ссылаться на локальные tiles,
glyphs и sprites. Локальные тайлы на этом этапе не поставляются.

Это временный источник по разрешению владельца для SPRINT 1, не постоянная
production-зависимость. Первичная загрузка и pan/zoom могут обращаться в интернет.
Клик/карточка используют локальный fixture и не делают сетевых запросов.
Публичные `tile.openstreetmap.org` серверы не используются.

## Demo GeoJSON

`frontend/src/data/demo/point.json` — один искусственный Point, `demo-object-1`.
Координаты `[30.3158, 59.9391]` заданы владельцем в примере для этого спринта.
Название и описание явно демонстрационные; точка не представляет городской объект.
Начиная с SPRINT 3 fixture добавляется в PostGIS явной командой
`docker compose exec backend python -m app.seed_demo`. Источник —
`development-fixture`, properties.demo=true; runtime использует только API.
Frontend fixture сохранён для regression tests, а не как fallback при сбое API.
Это не production geographic knowledge.

## MapLibre dependency

MapLibre GL JS 6.9.1 установлен через npm, лицензия BSD-3-Clause, собственные
TypeScript-типы; не требует React wrapper, платного API или provider key.
Совместимость проверена с React 19.3, TypeScript 6.0, Vite 8.3 и Node 24.21.
Перед установкой проверены npm metadata и публичные advisories:
[GHSA-jrc7-96c5-q579](https://github.com/maplibre/maplibre-gl-js/security/advisories/GHSA-jrc7-96c5-q579)
исправлен начиная с 6.4.1, установленная версия 6.9.1 включает исправление.
При установке npm audit: 0 известных уязвимостей. JS bundle с картой около
345 kB gzip; Vite предупреждает о размере raw chunk >500 kB. Предупреждение
не скрывается; оптимизация производительности не расширяет текущий спринт.

## SPRINT 2 — административные районы Санкт-Петербурга

Development dataset: `frontend/src/data/districts/spb-districts.json`.

- Геометрии получены 2026-09-15 одним lookup-запросом Nominatim из 18 отношений
  OpenStreetMap `admin_level=5`, перечисленных на странице
  [«Районы Санкт-Петербурга»](https://wiki.openstreetmap.org/wiki/RU:%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3/%D0%A0%D0%B0%D0%B9%D0%BE%D0%BD%D1%8B).
- Использованы relation IDs: 1114193, 1114252, 1114354, 1114806, 1114809,
  337424, 1114895, 363103, 1115082, 1115366, 338636, 368287, 1114905,
  367375, 1115367, 338635, 369514, 1114902. ID приложения имеет форму
  `district-osm-relation-<relation id>` и не зависит от названия.
- Snapshot содержит ровно 18 объектов: 15 Polygon и 3 MultiPolygon. Названия
  сверены с перечнем районов; длинные display address Nominatim удалены.
- Source: © OpenStreetMap contributors. License: [ODbL 1.0](https://www.openstreetmap.org/copyright).
  Attribution показывается в MapLibre AttributionControl.
- Nominatim использован только для однократного получения малого набора с
  собственным User-Agent согласно [Usage Policy](https://operations.osmfoundation.org/policies/nominatim/).
  Приложение не обращается к Nominatim в runtime.
- Свежесть — состояние OpenStreetMap на дату получения. Автоматическое обновление
  и гарантия официальной актуальности отсутствуют. Перед production-use требуется
  сверка с официальным реестром и воспроизводимый import/update process; это не
  входит в SPRINT 2.

GeoJSON является временным development snapshot. Его source boundary изолирован
в `data/districts/index.ts`, что позволяет в будущем заменить загрузку API/PostGIS.
