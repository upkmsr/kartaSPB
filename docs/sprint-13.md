# SPRINT 13 — Roads

Статус: **DONE**. Отдельный модуль автомобильной инфраструктуры поверх
canonical objects и Data Platform; routing не входит в спринт.

## Результат

- В PostGIS загружены 5 594 дорожных объекта OSM: 4 997 сегментов крупных
  дорог (`motorway`, `trunk`, `primary`), 557 съездов, 607 сегментов КАД,
  244 сегмента ЗСД и 40
  явно размеченных узлов `motorway_junction`. Сегменты и точки имеют стабильные
  ID по OSM type/ID; повторный импорт обновляет их без дублей.
- Миграция `0011_roads` добавляет специализированную таблицу `roads`, категории
  и частичный GiST индекс для дорог. Геометрия хранится в canonical
  `project_objects`: LineString для дорог и Point для узлов.
- `GET /api/roads` поддерживает bbox, тип, коридор, категорию и пагинацию;
  `/api/roads/viewport.geojson` выдаёт ограниченные GeoJSON-данные для текущей
  области карты. `/api/analysis/roads/nearest` возвращает ближайшую крупную
  дорогу, КАД, ЗСД и развязку с `method=straight-line`.
- Четыре независимые записи Layer Registry управляют крупными дорогами,
  КАД, ЗСД и развязками/съездами. КАД и ЗСД различаются цветом в Dark Urban.
  Дорожная геометрия загружается по viewport в MapLibre, а не целиком в React.

## Воспроизведение

```bash
docker compose up --build --wait
docker compose exec backend python -m app.roads
docker compose exec backend alembic current
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_roads.py
```

Подробности источников, дат и ограничений: [data-sources.md](data-sources.md).
Отсутствующий `toll` не означает бесплатную дорогу; расстояние по прямой не
равно расстоянию или времени поездки по сети.
