# SPRINT 8 — Metro

Статус: **DONE**. `app.metro` добавляет линии, станции и входы метро как
разные canonical объекты.

## Результат

- Снимок OSM от 2026-09-16 даёт 6 линий (MultiLineString), 72 станции и
  261 вход (Point). Оба направления линии с одним `ref` отображаются как одна
  линия; принадлежность станции линиям выводится из route members и тегов.
- Три слоя Layer Registry включаются независимо. Цвета линий нормализуются из
  данных источника, а выбор станции или входа открывает общую Object Card.
- `GET /api/analysis/metro/nearest?lon=...&lat=...` возвращает ближайшую
  станцию с расстоянием PostGIS и явным `method=straight-line`.

## Воспроизведение и проверка

```bash
docker compose exec backend python -m app.metro
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_metro.py
```

Тест проверяет состав снимка, геометрию, provenance и endpoint ближайшей
станции. Охват и атрибуция: [data-sources.md](data-sources.md).

## Ограничение

Расстояние по прямой не равно пешеходному маршруту или времени в пути.
Принадлежность станций линиям зависит от полноты OSM route relations.
