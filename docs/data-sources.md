# Источники данных

## SPRINT 1 — development basemap

Проверено 2026-09-15:

- Provider: [OpenFreeMap](https://openfreemap.org/), публичный бесплатный instance.
- Style: `https://tiles.openfreemap.org/styles/dark`, MapLibre Style Specification v8.
- Vector TileJSON: `https://tiles.openfreemap.org/planet` (точный URL тайлов задаёт provider).
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
Fixture не импортируется в PostGIS и не является production geographic knowledge.

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
