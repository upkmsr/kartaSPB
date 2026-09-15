# Архитектура

## SPRINT 0

- `frontend/`: React + TypeScript + Vite; UI shell и отдельный API client.
- `backend/app/`: FastAPI, конфигурация из environment, подключение SQLAlchemy/psycopg.
- `backend/migrations/`: Alembic, расширение PostGIS без предметных таблиц.
- `modules/`: место для будущих модулей; бизнес-модули пока не созданы.
- `docker-compose.yml`: PostGIS → migration job → API → nginx/frontend.
- `/api` проксируется через nginx (Compose) или Vite (локальная разработка).
  URL backend не зашит в React; браузер использует один origin.

Healthcheck БД ждёт финальный PostgreSQL-процесс после первичной инициализации
образа; это исключает запуск миграции во время промежуточного рестарта сервера.
Liveness не зависит от БД. Readiness возвращает 503 при недоступности PostGIS
или несовпадении версии миграции. При новых миграциях обновлять ожидаемую ревизию.
Запросы синхронные: FastAPI выполняет их в thread pool.
Ошибки подключения не раскрывают credentials в ответах или журналах.

## SPRINT 1 — Минимальная карта

- `frontend/src/config/map.ts`: начальный viewport, URL style JSON и attribution.
  Источник можно заменить на другой MapLibre-совместимый, в том числе same-origin
  self-hosted style, изменив конфигурацию и пересобрав frontend.
- `frontend/src/domain/mapObject.ts`: GeoJSON-based `MapObject`, `ObjectProperties`,
  `SelectedObject`; типы предметной области не зависят от MapLibre.
- `frontend/src/data/demo/point.json`: ровно один fixture с устойчивым ID.
- `frontend/src/map/mapLibreAdapter.ts`: MapLibre instance, viewport, controls,
  GeoJSON source, circle layer, map events. Клик передаёт только ID.
- `frontend/src/components/MapView.tsx`: DOM container, lifecycle, ResizeObserver,
  сообщения загрузки/ошибки. Unmount вызывает `map.remove()`; обычный rerender,
  смена callback и открытие/закрытие карточки не пересоздают карту.
- `App.tsx`: определяет объект по ID из собственного demo dataset и хранит
  `selectedObject`. Свойства из map event не становятся содержимым карточки.
- `ObjectCard.tsx`: отдельная React-карточка. Закрытие сбрасывает `selectedObject`
  в `null`. На mobile высота ограничена, содержимое прокручивается; attribution
  и навигационные controls остаются доступными.

Basemap и demo source разделены. Клик не делает API/геокодирование или запрос БД.
Внешняя подложка разрешена текущей командой владельца как временное development
решение; полноценный offline runtime пока не реализован. Backend и миграции
спринта 0 не изменены. CORE + MODULES сохраняется; следующие модули не создаются.
