# SPRINT 1 — Минимальная карта

## Реализация

- MapLibre GL JS 6.9.1 установлен через npm.
- Начальный viewport: Санкт-Петербург, `[30.3158, 59.9391]`, zoom 12.
- Development basemap: OpenFreeMap dark style, конфигурация отделена от React.
- Один искусственный GeoJSON Point: `demo-object-1`, отдельно от basemap и БД.
- MapLibre adapter передаёт stable ID, React хранит `selectedObject` и
  отображает отдельную закрываемую карточку.
- Map instance удаляется при unmount и не пересоздаётся при выборе объекта.

## Проверки

- frontend tests: PASS — 11.
- ESLint: PASS.
- TypeScript: PASS.
- production build: PASS.
- Docker Compose: PASS, `db`, `backend`, `frontend` healthy; `migrate` Exited (0).
- backend tests: PASS — 5, включая PostGIS integration.
- Ruff/mypy: PASS.
- Alembic: PASS — `0001_postgis (head)` current и head.

## Ограничения

- Basemap временно требует интернет; provider не предоставляет SLA.
- Vite сообщает о raw JS chunk >500 kB; gzip JS около 345 kB. Оптимизация
  загрузки относится к будущему performance этапу и не скрывает предупреждение.
- Fixture не является городским объектом и не импортируется в PostGIS.
