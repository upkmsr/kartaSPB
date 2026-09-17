# SPRINT 14 — Noise / Aviation / Helicopters

## Реализовано

- Миграция `0012_noise`: отдельные типы `road_noise`, `railway_noise`,
  `aviation_noise`, `helicopter_noise` и таблица `noise_sources` поверх canonical
  PostGIS objects. Для пространственных запросов создан GiST index.
- Дорожный набор получен повторяемым импортом из SPRINT 13 Roads. Это
  **estimated** / **LOW**: качественный класс *потенциала влияния* использует
  OSM `road_class` и число полос (motorway либо trunk с ≥4 полосами — high;
  остальные trunk/primary — medium; links — low). Это не физическая модель
  распространения шума и не оценка фактической экспозиции.
- Железнодорожный набор получен из реальных OSM `railway=rail` линий.
  Служебные spur/siding/yard/crossover исключены из первичного слоя, поскольку
  частота движения неизвестна. Это **unknown** / **MEDIUM** для положения пути,
  не для уровня шума.
- `intensity_db = NULL` для всех объектов. API не выдаёт отсутствие данных
  за 0 дБ. `/api/noise/availability` показывает `no_data` для авиации и
  вертолётов; `/api/analysis/noise/point` возвращает прямолинейные расстояния
  и `null` для неизвестных источников/интенсивности.
- Четыре независимых слоя в Layer Registry, bbox-загрузка в MapLibre, карточка
  с происхождением/датой/уверенностью, текстовая легенда и явный no-data status.

## Источники и ограничения

Железнодорожный OSM-снимок: [BBBike city PBF](https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.pbf),
дата OSM extract `2026-09-11T23:00:00Z`, bbox `30.042,59.796–30.630,60.071`.
Дорожный набор: уже импортированный [OSM Roads](sprint-13.md), снимки
`2026-07-15` и `2026-09-11`. Лицензия ODbL 1.0, © OpenStreetMap contributors;
использован только открытый снимок, платных API нет. Ограничения: неполное
покрытие за пределами city extract, неизвестный трафик, скорость движения,
подвижной состав, рельеф и экранирование.

Проверены [материалы Росавиации о территории Пулково](https://favt.gov.ru/dejatelnost-ajeroporty-i-ajerodromy-priaerodromnie-territorii/?id=3867)
и [сведения администрации Санкт-Петербурга о воздушном транспорте](https://www.gov.spb.ru/gov/otrasl/c_transport/vneshnij-transport/vozdushnyj-transport/).
Зоны воздушных подходов и ограничения воздушного пространства не являются
контурами авиационного шума. Публичных, машиночитаемых, лицензированных
контуров шума Пулково и проверенных вертолётных маршрутов для импорта не
установлено. Соответствующие слои пусты до появления надёжных данных.

Ни один класс цвета карты не следует трактовать как уровень дБ, санитарный
норматив или прогноз шума для адреса. Общий Noise Score не вычисляется.

## Воспроизведение

```bash
docker compose up --build --wait
docker compose exec backend python -m app.roads
docker compose exec backend python -m app.noise
docker compose exec backend alembic current
docker compose exec backend alembic heads
```

Импорт идемпотентен. История, ошибки и provenance сохраняются общим Data Platform.
