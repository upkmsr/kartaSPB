# Источники данных

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
