# SPRINT 11 — Kindergartens

Статус: **DONE**. `app.kindergartens` добавляет детские сады, специализированную
модель и пространственный анализ поверх общего canonical и ingestion CORE.

## Результат

- Снимок OSM от 2026-09-16 содержит 1 575 элементов; 1 503 именованных
  объекта пригодны для импорта. Каждый node/way/relation сохраняет свой OSM ID,
  а центры ways и relations не выдаются за входы в здания.
- Миграция `0009_kindergartens` добавила специализированные поля и категории
  `public`, `private`, `unknown`. Ownership берётся только из явного
  `operator:type`; confidence отражает заполненность данных.
- `GET /api/kindergartens` поддерживает bbox, тип оператора и limit;
  `/api/kindergartens/nearby` возвращает ближайший сад и подсчёт по типу
  оператора с `method=straight-line`. Слой и карточка используют общую карту.
- Официальные правила приёма представлены записью `text_rule` с URL в
  `kindergarten_admission_sources`, без придуманной геометрии.

## Воспроизведение и проверка

```bash
docker compose exec backend python -m app.kindergartens
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_kindergartens.py
```

Тест проверяет повторный импорт без дублей, PostGIS, provenance, API и
nearby-анализ. Источники и ограничения: [data-sources.md](data-sources.md).

## Ограничение

OSM не гарантирует полный перечень государственных или частных садов,
актуальные цены и наличие мест. Пространственный анализ не заменяет правила
комплектования.
