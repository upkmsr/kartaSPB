# SPRINT 7 — Nature

Статус: **DONE**. Изолированный модуль `app.nature` добавляет реальные зелёные
территории, водные объекты и нанесённые в OSM набережные.

## Результат

- Снимок именованных OSM ways от 2026-09-16 охватывает ограниченную область
  Петербурга. Теги классифицируются в `nature-green` и `nature-water`.
- Замкнутые ways становятся Polygon, открытые — LineString. Стабильные OSM ID,
  raw staging и provenance обрабатываются общим ingestion pipeline.
- В MapLibre есть отдельные fill/line слои зелёных территорий и воды;
  Layer Registry управляет видимостью и прозрачностью, категории — фильтрами.
  Клик открывает общую Object Card.

## Воспроизведение и проверка

```bash
docker compose exec backend python -m app.nature
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_nature.py
```

Тест проверяет не менее 1 000 записей двух категорий, Polygon и LineString,
валидность геометрии в PostGIS и импорт без ошибок.

## Ограничение

Снимок не включает все безымянные объекты и multipolygon relations; сплошной
аналитический полигон Финского залива не создан. Отдельный proximity API для
природы в этом модуле не реализован. Подробности: [data-sources.md](data-sources.md).
