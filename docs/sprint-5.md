# SPRINT 5 — Data Ingestion Framework

Статус: **DONE**. Миграция `0003_ingestion` добавила общую платформу загрузки
данных. Предметные модули используют её вместо собственных таблиц импорта.

## Результат

- `data_sources` хранит источник, URL, лицензию, attribution и приоритет;
  `ingestion_runs` — статус и счётчики запуска.
- `ingestion_staging` сохраняет исходную запись, нормализованную форму и
  результат проверки; `ingestion_errors` хранит ошибки валидации.
- Pipeline проверяет геометрию и ожидаемые границы, строит стабильный ID из
  source ID и record ID, делает upsert в canonical `project_objects` и записывает
  `object_provenance`. Повторная запись с тем же source record ID обновляет
  объект, а не создаёт новый.
- `app.ingestion.deduplicate` предоставляет нормализованный ключ сопоставления.
  Автоматическое объединение похожих объектов из разных источников не заявлено.
- `GET /api/import/status`, `/api/import/runs`, `/api/import/errors` дают
  read-only обзор импортов. Импорт выполняется отдельной CLI-командой, не внутри
  HTTP-запроса.

## Проверка

`backend/tests/test_ingestion.py` проверяет нормализацию, валидацию,
идемпотентность, staging, provenance и API. Интеграционная часть требует
запущенный PostGIS:

```bash
docker compose run --rm -e RUN_DB_TESTS=1 backend pytest -q tests/test_ingestion.py
```

## Ограничение

SPRINT 5 поставляет инфраструктуру. Реальный исходный геодатасет появляется
в SPRINT 6. Общая схема описана в [architecture.md](architecture.md).
