# SPRINT 10 — Schools

Статус: **DONE**. `app.schools` добавляет специализированную модель школ поверх
canonical objects, не дублируя платформу импорта.

## Результат

- Из снимка OSM от 2026-09-16 доступны 1 031 именованная школа, лицей или
  гимназия. OSM type/ID различает физические объекты; координаты ways и
  relations — центры, вычисленные источником.
- Миграция `0008_schools` создала таблицу `schools` с типом учреждения,
  ownership, адресом, контактами, датой источника и confidence. Отсутствующие
  значения вместимости, результатов и рейтинга остаются NULL.
- `GET /api/schools` поддерживает bbox и limit. Слой школ и Object Card используют
  общий Layer Registry и canonical API. Staging, provenance и повторный upsert
  выполняет Data Platform.
- `school_catchments` допускает проверенные MultiPolygon в будущем, но сейчас
  хранит только `address_list` и URL официальных правил. API `/api/schools/catchments`
  явно сообщает об отсутствии проверенной пространственной границы.

## Воспроизведение и проверка

```bash
docker compose exec backend python -m app.schools
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_schools.py
```

Тест проверяет идемпотентность, PostGIS-геометрию, provenance, bbox API и
неопределённость закреплённых территорий. Источники: [data-sources.md](data-sources.md).

## Ограничение

OSM не является официальным реестром школ. Адресные правила не превращаются
автоматически в полигоны и не дают гарантии приёма.
