# SPRINT 6 — Base OSM/Open Geodata

Статус: **DONE**. Добавлен воспроизводимый начальный импорт реальных данных
OpenStreetMap через общий pipeline SPRINT 5.

## Результат

- Адаптер `app.open_data` использует ограниченный запрос Overpass по отношениям
  административных районов Петербурга (`admin_level=5`). В репозитории хранится
  снимок из 18 отношений, собранный 2026-09-16.
- В canonical objects загружаются центры отношений, вычисленные источником.
  OSM type/ID формируют стабильную идентичность; лицензия ODbL и attribution
  регистрируются в Source Registry, а каждая запись получает provenance.
- Обычный запуск читает локальный снимок. `--refresh` повторяет тот же
  ограниченный запрос к Overpass; frontend во время работы читает PostGIS и
  не обращается к Overpass или публичному OSM tile server.

## Воспроизведение и проверка

```bash
docker compose exec backend python -m app.open_data
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_open_data.py
```

Тест проверяет реальные 18 записей, повторный импорт и provenance. Источник,
лицензия и метод сбора описаны в [data-sources.md](data-sources.md).

## Ограничение

Это центры районов, а не полные геометрии границ и не региональный OSM-экстракт.
Базовая подложка карты остаётся отдельным источником OpenFreeMap.
