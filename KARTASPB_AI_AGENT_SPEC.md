# KARTASPB — итоговое техническое задание для AI-агента

> **Статус:** Master Specification  
> **Проект:** KARTASPB  
> **Основная территория:** Санкт-Петербург и Ленинградская область  
> **Назначение:** постоянная инструкция AI-кодеру для поэтапной разработки проекта  
> **Главный принцип:** после каждого этапа приложение должно оставаться запускаемым и рабочим.

---

# 0. Роль AI-агента

Ты являешься ведущим software architect, GIS developer, backend developer, frontend developer и data engineer проекта **KARTASPB**.

Твоя задача — поэтапно разработать персональную GIS-систему для анализа Санкт-Петербурга и Ленинградской области с возможностью оценивать территории и конкретные точки по транспортной доступности, школам, детским садам, медицине, природе, дорогам, шуму, пользовательским местам и другим факторам.

Проект **не является сервисом недвижимости**.

Без отдельного явного решения владельца проекта запрещено добавлять:

- поиск квартир;
- объявления;
- каталог ЖК;
- цены недвижимости;
- риелторские функции;
- ипотечные функции.

---

# 1. Главная цель продукта

Система должна помогать пользователю отвечать на вопрос:

> **«Насколько конкретное место подходит мне для жизни и почему?»**

Пользователь должен иметь возможность:

- открыть интерактивную карту;
- выбрать один или несколько районов;
- включать и выключать независимые GIS-слои;
- просматривать реальные объекты;
- искать адреса и объекты;
- кликать по объектам и точкам;
- получать карточки объектов;
- создавать собственные точки, области и маршруты;
- сравнивать территории;
- задавать приоритеты факторов;
- получать итоговый score;
- видеть объяснение score;
- анализировать доступность школ, детских садов, медицины, метро, транспорта, парков, воды и дорог;
- учитывать шум;
- рассчитывать время до личных точек;
- сохранять пользовательские заметки и оценки;
- видеть происхождение, дату и качество исходных данных.

---

# 2. Критические правила работы AI-агента

## 2.1. Работать поэтапно

Не пытайся реализовать весь проект одним большим изменением.

Перед каждым спринтом:

1. изучи текущий репозиторий;
2. проверь архитектуру;
3. прочитай актуальные README и docs;
4. проверь зависимости;
5. проверь миграции;
6. составь короткий план изменений;
7. меняй только относящиеся к текущей задаче части.

После каждого спринта:

1. запусти backend;
2. запусти frontend;
3. выполни миграции;
4. запусти тесты;
5. выполни lint/type-check;
6. проверь UI;
7. проверь `git diff`;
8. исправь регрессии;
9. обнови документацию;
10. только затем считай спринт завершённым.

## 2.2. Не ломать работающий код

Не переписывай работающий модуль только потому, что его можно написать иначе.

Рефакторинг допустим, если он необходим текущей задаче, исправляет подтверждённую проблему или отдельно обоснован и протестирован.

## 2.3. Не выдумывать данные

Никогда не придумывай:

- координаты;
- адреса;
- рейтинги;
- цены;
- вместимость;
- результаты экзаменов;
- маршруты;
- уровни шума;
- расписания;
- источники;
- URL;
- даты;
- характеристики объектов.

Если значение неизвестно, использовать `NULL`, `unknown` или эквивалентное состояние.

UI должен показывать **«Нет данных»**, а не искусственное значение.

## 2.4. Не имитировать успешную работу

Если import завершился ошибкой, нельзя сообщать о полном успехе.

Importer должен показывать реальные числа:

- найдено;
- добавлено;
- обновлено;
- пропущено;
- объединено как дубликаты;
- ошибок;
- предупреждений.

## 2.5. Интернет не является runtime-зависимостью карты

Обычная работа карты не должна требовать интернет-запроса при каждом:

- pan/zoom;
- переключении слоя;
- изменении фильтра;
- изменении веса;
- клике по объекту.

Интернет используется отдельно для первоначального импорта, обновления данных, внешнего геокодирования и внешней маршрутизации, если выбран внешний provider.

---

# 3. Картографический стек

Использовать **MapLibre GL JS** как основной картографический движок.

Без отдельного согласования не использовать:

- Google Maps SDK;
- Mapbox GL JS;
- другие коммерческие картографические SDK.

MapLibre должен быть независим от конкретного поставщика тайлов.

---

# 4. Географические данные и базовая карта

Основная географическая основа:

- OpenStreetMap;
- совместимые открытые геоданные;
- официальные открытые геоданные;
- собственные данные проекта.

OpenStreetMap считать источником данных, а не гарантированно бесплатным production tile server.

Требования:

- не привязывать frontend к публичным OSM tile servers;
- tile provider должен быть заменяемым;
- provider config не хранить внутри React-компонентов;
- предусмотреть self-hosted/local tile source;
- соблюдать attribution;
- фиксировать licensing и rate limits;
- не подключать платные providers без явного согласования.

---

# 5. Целевая география

Основная территория:

1. Санкт-Петербург;
2. Ленинградская область.

Начальный viewport — Санкт-Петербург.

Архитектура не должна мешать добавлению других регионов в будущем.

---

# 6. Базовый технологический стек

## Frontend

```text
React
TypeScript
MapLibre GL JS
```

Допускается Next.js, если он действительно полезен проекту.

## Backend

```text
Python
FastAPI
```

## Database

```text
PostgreSQL
PostGIS
```

## GIS/Data processing

По необходимости:

```text
GeoPandas
Shapely
Pandas
PyProj
GDAL ecosystem
```

## Infrastructure

```text
Docker
Docker Compose
Git
GitHub
```

Предпочтительный локальный запуск:

```bash
docker compose up
```

---

# 7. Архитектура: CORE + MODULES

## 7.1. CORE

Core отвечает за:

- запуск и конфигурацию приложения;
- MapLibre shell;
- layer registry;
- PostgreSQL/PostGIS connection;
- общую модель пространственных объектов;
- source/provenance system;
- spatial grid;
- scoring framework;
- cache;
- общие API utilities;
- UI shell;
- настройки;
- user profiles;
- logging/error handling;
- module lifecycle;
- общие типы и контракты.

Core не должен содержать бизнес-логику конкретной школы, клиники или маршрута.

## 7.2. MODULES

```text
modules/
├── transport/
├── metro/
├── schools/
├── kindergartens/
├── medical/
├── nature/
├── roads/
├── noise/
├── aviation/
├── helicopters/
├── user_data/
├── routing/
├── scoring/
├── analytics/
└── data_import/
```

Будущие модули:

```text
everyday_infrastructure/
air_quality/
cycling/
parking/
sports/
retail/
```

## 7.3. Типовая структура модуля

```text
module/
├── models/
├── schemas/
├── services/
├── repositories/
├── importers/
├── processors/
├── api/
├── map/
├── tests/
├── migrations/
└── README.md
```

Не делать прямые хаотичные обращения к внутренностям другого модуля.

---

# 8. Разделение UI, логики и карты

```text
UI
│
├── React components
│
Application logic
│
├── objects
├── categories
├── search
├── filters
├── layers
├── routes
├── drawing
├── scoring
└── user data
│
Map adapter
│
└── MapLibre GL JS
│
Geodata
│
├── GeoJSON
├── PostGIS
├── vector tiles
└── external datasets
│
Providers
│
├── tiles
├── geocoding
└── routing
```

Не помещать бизнес-логику непосредственно в MapLibre event handlers.

React управляет состоянием приложения. MapLibre отвечает за визуализацию карты и map events.

---

# 9. Пространственные объекты

Пользовательские и проектные объекты должны быть отделены от basemap.

Для API/frontend предпочтительно GeoJSON.

Пример:

```json
{
  "id": "stable-unique-id",
  "name": "Название объекта",
  "category": "category_id",
  "description": "Описание",
  "geometry": {
    "type": "Point",
    "coordinates": [30.3158, 59.9391]
  }
}
```

Поддерживаемые геометрии:

```text
Point
MultiPoint
LineString
MultiLineString
Polygon
MultiPolygon
```

Основное долгосрочное spatial-хранилище — PostGIS.

GeoJSON — основной формат обмена с frontend и внешними инструментами, но не обязательный единственный формат хранения.

---

# 10. Категории объектов

Категория — отдельная сущность, а не только текстовая подпись.

Например:

```text
museum
park
restaurant
historical
transport
school
kindergarten
medical
user
other
```

Категории используются для фильтрации, слоёв, поиска, стилизации, карточек и аналитики.

---

# 11. Карточка объекта

При клике на объект пользователь получает карточку или боковую панель.

MapLibre только сообщает о выборе объекта.

React хранит `selectedObject` и отображает карточку.

Карточка может содержать:

- название;
- тип;
- категорию;
- адрес;
- характеристики;
- источники;
- дату обновления;
- пользовательскую оценку;
- заметки;
- доступность;
- связанные объекты;
- действия.

---

# 12. Система слоёв

Пример:

```text
Базовая карта
│
├── Районы
├── Объекты проекта
├── Метро
├── Наземный транспорт
├── Школы
├── Детские сады
├── Медицина
├── Природа
├── Вода
├── Дороги
├── Шум
├── Авиация
├── Вертолёты
├── Пользовательские точки
├── Пользовательские области
└── Пользовательские маршруты
```

Каждый слой по возможности поддерживает:

- show/hide;
- opacity;
- filter;
- style;
- z-order;
- legend;
- независимую загрузку данных.

Не объединять все данные в один монолитный layer.

---

# 13. Поиск

## 13.1. Поиск собственных объектов

Работает по собственной базе и не зависит от внешнего geocoder.

Искать как минимум по:

- названию;
- адресу;
- категории;
- типу.

## 13.2. Геокодирование

Создать заменяемый интерфейс:

```text
GeocoderProvider
```

Допускается Nominatim, если способ использования соответствует актуальным правилам выбранного сервиса.

Search UI не должен знать детали Nominatim.

---

# 14. Фильтрация

Минимальные фильтры:

- категория;
- тип;
- район;
- источник;
- official/user;
- видимость слоёв.

Использовать MapLibre filters и backend query вместо ручной полной перерисовки карты.

---

# 15. Районы

Пользователь может выбрать один или несколько районов.

После выбора:

- активные районы выделяются;
- невыбранные территории затемняются;
- детальные данные загружаются по selected districts/viewport;
- аналитика может ограничиваться выбранной территорией;
- набор районов можно сохранить как preset.

---

# 16. Визуальный стиль

Целевое направление:

**Dark Urban / Racing HUD / GTA-NFS-inspired GIS**

Это референс атмосферы, а не копирование интерфейса конкретной игры.

Принципы:

- тёмно-синий/графитовый фон;
- тёмная вода;
- серые здания;
- умеренная прозрачность;
- neon-like highlight выбранных объектов;
- контрастные маршруты;
- стандартные цвета линий метро;
- полупрозрачные панели;
- аккуратный glow;
- минимум визуального шума;
- smooth transitions.

3D buildings допустимы, но не являются MVP-блокером.

---

# 17. Responsive/mobile

Frontend должен быть responsive с первого этапа.

Поддержка:

- desktop;
- tablet;
- mobile.

Бизнес-логику не связывать жёстко с desktop DOM layout.

---

# 18. Пользовательские области

Пользователь должен уметь:

- рисовать Polygon;
- при необходимости рисовать LineString;
- редактировать;
- удалять;
- сохранять;
- загружать;
- переименовывать.

Map/drawing library отвечает за редактирование geometry, application layer — за сохранение и бизнес-логику.

---

# 19. Пользовательские маршруты

Маршрут хранится как `LineString`.

Не связывать маршрут с конкретным routing provider.

Создать интерфейс:

```text
RoutingProvider
```

Возможные open-source движки для отдельного выбора:

- OSRM;
- Valhalla;
- GraphHopper;
- другой совместимый open-source engine.

Перед выбором сравнить self-hosting, лицензию, транспортные профили, производительность и сложность обновления routing graph.

---

# 20. Персональные точки

Пользователь может создавать:

```text
Дом
Работа
Школа ребёнка
Родители
Спортзал
Друзья
Другое
```

Поля:

- id;
- название;
- тип;
- geometry;
- priority/weight;
- note.

---

# 21. Data Intelligence Layer

Общая схема:

```text
INTERNET / OPEN DATA
        ↓
SOURCE REGISTRY
        ↓
COLLECTORS
        ↓
RAW / STAGING
        ↓
NORMALIZER
        ↓
GEOCODER
        ↓
DEDUPLICATOR
        ↓
VALIDATOR
        ↓
CANONICAL POSTGIS TABLES
        ↓
SPATIAL PROCESSING
        ↓
GRID FEATURES
        ↓
FACTOR SCORES
        ↓
API / VECTOR TILES
        ↓
FRONTEND
```

---

# 22. Source Registry

Минимальные поля источника:

```text
id
name
type
url
license
attribution
priority
enabled
last_checked_at
notes
```

Ограничения использования источника должны быть документированы.

---

# 23. Первоначальный автоматический сбор данных

Initial data load — обязательная часть проекта.

Для каждого модуля агент должен:

1. найти допустимые источники;
2. реализовать importer/adapter;
3. загрузить доступные данные;
4. нормализовать;
5. геокодировать при необходимости;
6. устранить дубликаты;
7. валидировать;
8. сохранить в PostGIS;
9. сохранить provenance;
10. сформировать отчёт импорта.

Пользователь не должен вручную создавать основную базу массовых объектов.

---

# 24. Приоритет источников

## HIGH

- государственные реестры;
- официальные open data;
- муниципальные источники;
- официальный сайт организации.

## MEDIUM

- OpenStreetMap/open geodata;
- несколько независимых совпадающих источников;
- качественные официальные каталоги.

## LOW

- агрегаторы;
- каталоги;
- сайты отзывов;
- неполные вторичные источники.

## UNKNOWN

Недостаточно информации.

---

# 25. Provenance и качество данных

Минимально хранить:

```text
source_id
source_record_id
source_url
collected_at
last_verified_at
confidence
```

Для особо важных полей желательно field-level provenance.

Пример:

```text
rating
rating_source_id
rating_collected_at
```

Confidence:

```text
HIGH
MEDIUM
LOW
UNKNOWN
```

---

# 26. Обновление данных

Поддерживать:

```text
initial import
incremental import
manual refresh
source-specific refresh
```

Хранить:

```text
first_seen_at
last_seen_at
last_checked_at
last_changed_at
stale
```

Importer должен быть idempotent.

---

# 27. Дедупликация

Использовать entity resolution.

Например:

```text
СМ-Клиника
СМ Клиника
СМ-КЛИНИКА
```

могут быть одной организацией, но разные филиалы должны оставаться разными географическими объектами.

Использовать сочетание:

- normalized name;
- address;
- coordinates;
- phone;
- official id;
- website;
- spatial distance.

Сохранять aliases.

---

# 28. GIS-валидация

После импорта проверять:

- coordinate range;
- порядок longitude/latitude;
- geometry validity;
- ожидаемую географию;
- подозрительные выбросы.

Плохой объект помечать, например:

```text
validation_status = invalid
```

а не молча использовать в аналитике.

---

# 29. Nature

Содержит:

- парки;
- сады;
- скверы;
- леса;
- зелёные зоны;
- набережные;
- реки;
- каналы;
- озёра;
- пруды;
- Финский залив.

Расчёты:

- distance to nearest green area;
- green coverage;
- distance to water;
- water coverage;
- embankment accessibility.

---

# 30. Metro

Содержит:

- линии;
- станции;
- входы/выходы;
- пересадочные узлы.

Для точки рассчитывать:

- расстояние до ближайшей станции;
- walking/network distance;
- walking time;
- количество доступных станций;
- количество линий;
- доступность пересадок.

Не ограничиваться радиусом, если доступна транспортная сеть.

---

# 31. Наземный транспорт

Содержит:

- автобусы;
- трамваи;
- троллейбусы;
- остановки;
- маршруты;
- направления.

Пользователь может независимо включать типы и маршруты.

Для точки рассчитывать:

- ближайшие остановки;
- количество остановок;
- количество маршрутов;
- количество направлений;
- walking distance/time.

---

# 32. Schools

Собрать максимально полный набор:

- школы;
- лицеи;
- гимназии;
- специализированные школы;
- частные школы.

По возможности хранить:

- название;
- тип;
- адрес;
- coordinates;
- official id;
- website;
- rating;
- review count;
- год строительства;
- капитальный ремонт;
- вместимость;
- загрузку;
- правила приёма;
- закреплённую территорию;
- вступительные испытания;
- стоимость частного обучения;
- результаты ЕГЭ;
- достижения/олимпиады;
- provenance.

Недоступное не выдумывать.

---

# 33. School catchment

Если доступны официальные территории:

- хранить Polygon/MultiPolygon;
- индексировать в PostGIS;
- отображать отдельным слоем;
- определять попадание выбранной точки.

Нельзя утверждать гарантированное право зачисления без подтверждённых актуальных правил.

---

# 34. Kindergartens

Включить государственные и частные детские сады.

По возможности хранить:

- название;
- тип;
- адрес;
- coordinates;
- вместимость;
- группы;
- загрузку;
- год строительства;
- ремонт;
- рейтинг;
- отзывы;
- стоимость частного сада;
- правила приёма;
- provenance.

---

# 35. Medical

Собрать полноценный медицинский слой.

Категории:

- государственные поликлиники;
- детские поликлиники;
- больницы;
- специализированные центры;
- частные многопрофильные клиники;
- диагностические центры;
- лаборатории;
- стоматологии;
- женские консультации;
- профильные центры;
- травмпункты;
- круглосуточные учреждения;
- аптеки;
- пункты/подстанции скорой помощи, если есть допустимые open data.

Примеры сетей:

- СМ-Клиника;
- Немецкая семейная клиника.

Это только примеры. Не ограничивать сбор указанными брендами.

По возможности хранить:

- name;
- type;
- specialization;
- address;
- geometry;
- hours;
- 24/7;
- phone;
- website;
- services;
- rating;
- review_count;
- source;
- collected_at.

---

# 36. Medical score

Для клетки/точки рассчитывать по доступным данным:

- distance to nearest facility;
- number of facilities nearby;
- reachable facilities within N minutes;
- public medicine availability;
- private medicine availability;
- 24/7 availability;
- diagnostics;
- laboratories;
- dentistry;
- specialized care.

---

# 37. Roads

Содержит:

- магистрали;
- крупные дороги;
- КАД;
- ЗСД;
- платные дороги;
- въезды;
- съезды;
- развязки.

Расчёты:

- distance to major road;
- distance to KAD;
- distance to ZSD;
- interchange accessibility;
- car travel time to user destinations.

---

# 38. Noise

Не объединять все источники шума.

```text
road_noise
railway_noise
aviation_noise
helicopter_noise
```

Желательно хранить интенсивность и тип оценки:

```text
measured
modeled
estimated
unknown
```

Показывать confidence.

---

# 39. Helicopters

Вертолётные маршруты/коридоры — отдельный слой.

Хранить:

- geometry;
- source;
- validity date;
- confidence.

Если достоверной геометрии нет, нельзя изображать предположение как подтверждённый маршрут.

---

# 40. Spatial Grid

Для аналитики использовать предварительно рассчитанную сетку.

Размер конфигурируемый:

```text
50 × 50 m
100 × 100 m
200 × 200 m
```

Начальный вариант: **100 × 100 m**.

Каждая клетка имеет стабильный id и geometry.

Feature values, например:

```text
metro_feature
transport_feature
school_feature
kindergarten_feature
medical_feature
nature_feature
water_feature
road_feature
noise_feature
```

Raw feature и итоговый score логически разделять.

---

# 41. Scoring Engine

Каждый фактор нормализуется, например, в диапазон `0..100`.

```text
total_score = Σ(normalized_factor × user_weight)
```

Изменение веса:

- не запускает import;
- не запускает geocoding;
- не выполняет полный spatial recompute;
- использует precomputed features.

---

# 42. Missing data в scoring

`NULL` не равно `0` и не равно `100`.

Missing values обрабатывать явно.

Результат должен включать:

- score;
- completeness;
- confidence;
- отсутствующие факторы.

---

# 43. Explainable Score

При выборе точки показывать общий результат и вклад факторов.

Пример:

```text
Итог: 87 / 100

Метро          +18
Школы          +14
Медицина       +12
Парки          +10
Вода            +8
Транспорт       +7
Шум             -5
Дороги          -3
```

Показывать:

- почему хорошо;
- почему плохо;
- какие данные отсутствуют;
- насколько результат надёжен.

Причины вычисляются из реальных факторов, а не генерируются произвольно.

---

# 44. Score Profiles

Предусмотреть профили:

```text
family_with_children
without_car
quiet_life
work_in_center
custom
```

Пользователь может менять веса, сохранять, копировать и удалять профиль.

---

# 45. Heatmaps

Поддержать heatmap для:

- метро;
- транспорта;
- школ;
- детсадов;
- медицины;
- природы;
- воды;
- дорог;
- шума;
- итогового score.

Heatmap строится из подготовленных значений, а не выполняет тяжёлый пересчёт по каждому движению карты.

---

# 46. Isochrones

Для выбранной точки поддерживать:

```text
5 min
10 min
15 min
20 min
30 min
```

Режимы:

- walking;
- car;
- public transport, если routing model это поддерживает.

Изохрона — network reachability, а не круг фиксированного радиуса.

---

# 47. Commute Analysis

Для пользовательских destinations рассчитывать travel time.

Каждая destination имеет вес.

Пример:

```text
Work      40%
School    30%
Parents   20%
Gym       10%
```

Это позволяет оценивать кандидатную точку относительно личной географии пользователя.

---

# 48. User Observations

Пользователь может добавлять:

- оценку 1–10;
- дату визита;
- текстовую заметку;
- теги;
- фотографии/attachments;
- плюсы;
- минусы.

Примеры тегов:

```text
понравилось
шумно
очередь
хорошая территория
плохой подъезд
```

---

# 49. Official Data vs User Data

Официальные/внешние данные и пользовательские данные разделять.

Повторный импорт внешних данных никогда не должен удалять или перезаписывать пользовательские наблюдения.

Пользовательская оценка может влиять на персональный score только как отдельный пользовательский фактор.

---

# 50. Сравнение

Пользователь может сравнивать:

- точки;
- районы;
- сохранённые сценарии.

Сравнение должно использовать одинаковую методологию факторов.

---

# 51. База данных

Ориентировочные сущности:

```text
districts
categories
places

sources
source_records
source_field_values
ingestion_runs
ingestion_errors
object_aliases
data_quality

schools
school_catchments
kindergartens
medical_facilities
medical_services

metro_lines
metro_stations
metro_entrances
transit_routes
transit_stops

roads
road_interchanges
green_areas
water_objects
noise_sources
helicopter_corridors

grid_cells
factor_definitions
factor_features
factor_scores

score_profiles
score_weights

user_destinations
user_observations
user_geometries

route_cache
isochrone_cache
layer_config
app_settings
```

Это ориентир, а не требование создавать лишние таблицы без необходимости.

---

# 52. Spatial Indexes

Подходящие geometry columns индексировать.

Критические операции:

- contains;
- intersects;
- distance;
- nearest;
- bbox;
- viewport query;
- district filtering.

---

# 53. API

Разделять API по предметным областям.

```text
/api/districts
/api/objects
/api/categories
/api/search
/api/schools
/api/kindergartens
/api/medical
/api/metro
/api/transport
/api/nature
/api/roads
/api/noise
/api/scoring
/api/analytics
/api/routing
/api/user
/api/import
```

Не создавать один гигантский универсальный endpoint.

---

# 54. Data Import API / Jobs

Минимально предусмотреть административный механизм:

```text
POST /api/import/start
GET  /api/import/status
GET  /api/import/runs
GET  /api/import/errors
POST /api/import/module/{module}
POST /api/import/source/{source}
```

Длительный import не должен блокировать HTTP request на часы.

Использовать worker/background job/отдельный process или CLI.

---

# 55. Логирование импорта

Каждый run сохраняет:

```text
started_at
finished_at
status
source
module
objects_found
objects_inserted
objects_updated
objects_skipped
duplicates
warnings
errors
```

---

# 56. Cache

Кэшировать дорогие операции:

- spatial aggregation;
- score inputs;
- vector tiles;
- routes;
- isochrones;
- expensive analytics.

Cache должен иметь invalidation/versioning.

---

# 57. Производительность

Не загружать все детальные объекты города в frontend при старте.

Использовать по необходимости:

- viewport queries;
- district queries;
- clustering;
- vector tiles;
- lazy loading;
- spatial indexes;
- precomputation;
- cache.

---

# 58. Vector Tiles и локальная карта

Архитектура должна позволять использовать:

- vector tiles;
- PMTiles;
- self-hosted tile server;
- другой MapLibre-compatible source.

Tile source не хранить жёстко в компонентах.

После первоначальной подготовки данных основные функции желательно сделать доступными без постоянного интернет-соединения.

---

# 59. Лицензии и Attribution

Для каждого внешнего dataset/provider фиксировать:

- license;
- attribution requirements;
- production restrictions;
- commercial restrictions;
- update requirements.

Не обходить robots.txt, API restrictions, authentication, licensing и Terms of Service.

---

# 60. npm и зависимости

Frontend-библиотеки устанавливать через npm.

В Git хранить:

```text
package.json
package-lock.json
source code
config
documentation
required static assets/data
```

Не коммитить:

```text
node_modules
.env secrets
API keys
credentials
temporary files
build cache
```

---

# 61. Перед новой зависимостью

Проверить:

1. действительно ли она нужна;
2. нельзя ли решить задачу текущим стеком;
3. активность проекта;
4. лицензию;
5. размер;
6. security history;
7. compatibility;
8. нужен ли внешний API;
9. vendor lock-in.

---

# 62. Git

После логически завершённого этапа:

1. запустить проверки;
2. проверить `git status`;
3. проверить `git diff`;
4. удалить accidental files;
5. сделать понятный commit;
6. push, если remote настроен и push разрешён.

Примеры:

```text
feat(map): add MapLibre shell
feat(districts): add district selection
feat(data): add source registry
feat(metro): add metro module
feat(schools): add school importer
fix(scoring): handle missing factor values
```

---

# 63. Secrets

Хранить secrets только через environment/secrets.

Создать `.env.example` без реальных значений.

Никогда не выводить секреты полностью в logs.

---

# 64. Testing

Для модулей:

- unit tests;
- integration tests;
- API tests.

Для GIS:

- geometry validity;
- coordinate bounds;
- contains/intersects;
- distance;
- nearest object;
- catchment lookup;
- score normalization.

Для importers:

- parsing;
- idempotency;
- deduplication;
- invalid rows;
- provenance.

---

# 65. Документация

Поддерживать:

```text
README.md
docs/architecture.md
docs/data-sources.md
docs/modules.md
docs/scoring.md
docs/development.md
CHANGELOG.md
```

Этот файл — master requirements. Детали реализации дополнительно фиксируются в docs.

---

# 66. Рекомендуемая структура репозитория

```text
KARTASPB/
├── frontend/
├── backend/
├── modules/
├── data/
├── scripts/
├── infra/
├── docs/
├── tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── AI_AGENT_SPEC.md
```

Допускается более подходящая структура, если она обоснована.

---

# 67. SPRINT 0 — Repository & Architecture

Сделать:

- базовую структуру;
- Docker;
- frontend;
- backend;
- PostgreSQL/PostGIS;
- health checks;
- config;
- README;
- lint/test infrastructure.

Критерий: `docker compose up` запускает рабочий skeleton.

---

# 68. SPRINT 1 — Минимальная карта

Реализовать только:

```text
MapLibre
+
карта Санкт-Петербурга
+
один test GeoJSON object
+
click
+
React object card
```

Критерии:

- карта открывается;
- объект отображается;
- клик выбирает объект;
- карточка отображается;
- MapLibre и React state разделены.

---

# 69. SPRINT 2 — Districts & Layers

Реализовать:

- районы;
- district selection;
- dimming;
- layer registry;
- show/hide;
- opacity;
- z-order.

---

# 70. SPRINT 3 — Core Objects, Categories, Filters

Реализовать:

- canonical object model;
- categories;
- object API;
- filtering;
- project search.

---

# 71. SPRINT 4 — Search & Geocoding Abstraction

Реализовать:

- собственный поиск;
- `GeocoderProvider`;
- один допустимый provider;
- provider-independent UI.

---

# 72. SPRINT 5 — Data Ingestion Framework

Реализовать:

- source registry;
- ingestion runs;
- staging;
- normalizer;
- validator;
- deduplicator;
- importer logs;
- provenance.

---

# 73. SPRINT 6 — Base OSM/Open Geodata

Реализовать выбранный механизм первоначальной загрузки, обновления, хранения и attribution.

Не привязывать runtime карты к публичному OSM tile server.

---

# 74. SPRINT 7 — Nature

Добавить green areas, water, embankments и базовые proximity features.

---

# 75. SPRINT 8 — Metro

Добавить линии, станции, входы, layers и accessibility features.

---

# 76. SPRINT 9 — Surface Transport

Добавить stops, routes, directions, layer toggles и transport features.

---

# 77. SPRINT 10 — Schools

Добавить school importer, canonical data, provenance, layer и catchments, если доступны.

---

# 78. SPRINT 11 — Kindergartens

Добавить importer, data model, layer и analytics.

---

# 79. SPRINT 12 — Medical

Добавить public/private clinics, diagnostics, labs, dentistry, pharmacies и emergency/24h where supported.

Выполнить реальный initial import.

---

# 80. SPRINT 13 — Roads

Добавить major roads, KAD, ZSD, interchanges и accessibility features.

---

# 81. SPRINT 14 — Noise / Aviation / Helicopters

Добавить отдельные layers/modules.

Не подменять отсутствие данных выдуманной моделью.

---

# 82. SPRINT 15 — Drawing & User Geometries

Добавить Point/Polygon/LineString, edit/delete/save.

---

# 83. SPRINT 16 — Routing

Добавить `RoutingProvider`, один routing engine, user routes и route cache.

---

# 84. SPRINT 17 — Spatial Grid

Добавить configurable grid, feature preprocessing, indexes и batch processing.

---

# 85. SPRINT 18 — Scoring

Добавить factor definitions, normalization, weights, profiles, total score и missing-data policy.

---

# 86. SPRINT 19 — Explainability & Heatmap

Добавить heatmaps, score breakdown, reasons, confidence и completeness.

---

# 87. SPRINT 20 — User Observations

Добавить notes, ratings, tags, visits и attachments.

Гарантировать сохранность пользовательских данных при reimport.

---

# 88. SPRINT 21 — Personal Destinations & Isochrones

Добавить personal places, travel-time analysis, isochrones и weighted commute.

---

# 89. SPRINT 22 — Comparison & Analytics

Добавить comparison, saved scenarios и analytics UI.

---

# 90. SPRINT 23 — Responsive / Mobile QA

Проверить desktop/tablet/mobile, touch controls, panels и map interaction.

---

# 91. SPRINT 24 — Performance & Offline

Оптимизировать queries, indexes, cache, vector tiles, lazy loading и local data behavior.

---

# 92. SPRINT 25 — Backup / Export / Final QA

Добавить:

- DB backup;
- restore;
- GeoJSON export;
- CSV export;
- screenshot/export карты;
- полный test suite;
- final docs.

PDF export может быть отдельным будущим модулем.

---

# 93. Acceptance Criteria MVP

MVP принимается, если:

- приложение воспроизводимо запускается;
- MapLibre работает;
- Санкт-Петербург открывается;
- tile provider абстрагирован;
- районы выбираются;
- невыбранные районы затемняются;
- project objects отделены от basemap;
- объект кликабелен;
- карточкой управляет React;
- categories работают;
- filters работают;
- own object search работает;
- geocoder provider заменяемый;
- layers независимы;
- PostGIS используется для spatial data;
- import framework хранит provenance;
- importer не выдумывает значения;
- user data отделены от external data;
- UI responsive;
- tests проходят.

---

# 94. Acceptance Criteria расширенной версии

Дополнительно:

- реальные данные загружаются importers;
- metro работает;
- surface transport работает;
- schools работают;
- kindergartens работают;
- medical работает;
- private clinics не ограничены фиксированным списком;
- nature работает;
- roads работают;
- noise layers разделены;
- helicopter data имеют provenance;
- grid рассчитана;
- factor scores рассчитаны;
- weights меняются без re-fetch;
- heatmap работает;
- explainable score работает;
- confidence/completeness видимы;
- personal points работают;
- user observations переживают reimport;
- routing provider заменяемый;
- isochrones network-based;
- comparison работает;
- основные сценарии usable на mobile.

---

# 95. Запреты

Без явного согласования нельзя:

- менять MapLibre на другой SDK;
- подключать платный provider;
- создавать vendor lock-in;
- интегрировать недвижимость;
- использовать fake production data;
- коммитить secrets;
- коммитить `node_modules`;
- смешивать official/user data;
- обходить правила внешних сайтов;
- выдавать предположение за подтверждённый GIS-объект;
- жёстко связывать UI с geocoder/router;
- хранить массовые координаты в React source;
- загружать весь город огромным GeoJSON при каждом старте;
- пересчитывать весь город при каждом изменении веса.

---

# 96. Критическое правило картографического стека

Базовое решение проекта:

> **MapLibre GL JS + OpenStreetMap/open geodata + GeoJSON/PostGIS + open-source/free geocoding и routing solutions.**

Не менять это решение самостоятельно.

Если изменение необходимо, сначала подготовить обоснование:

1. почему текущий стек не подходит;
2. предлагаемое решение;
3. преимущества;
4. недостатки;
5. лицензия;
6. стоимость;
7. vendor lock-in;
8. сложность миграции;
9. возможность возврата.

До одобрения владельца миграцию не выполнять.

---

# 97. Формат отчёта AI-агента после спринта

```text
SPRINT: XX — Name

Сделано:
- ...

Изменённые файлы:
- ...

Миграции:
- ...

API:
- ...

Проверки:
- backend: PASS/FAIL
- frontend: PASS/FAIL
- tests: PASS/FAIL
- lint: PASS/FAIL
- typecheck: PASS/FAIL

Известные ограничения:
- ...

Следующий рекомендуемый этап:
SPRINT XX
```

---

# 98. Definition of Done

Задача завершена только если:

- код реализован;
- приложение запускается;
- миграции применяются;
- нет новых критических ошибок;
- tests/lint/type-check прошли либо блокер явно задокументирован;
- данные не сфабрикованы;
- docs обновлены;
- `git diff` проверен;
- изменения логически изолированы.

---

# 99. Главный пользовательский сценарий

```text
Открыть KARTASPB
        ↓
Выбрать районы
        ↓
Включить нужные слои
        ↓
Найти адрес или точку
        ↓
Посмотреть окружающие объекты
        ↓
Настроить веса факторов
        ↓
Увидеть heatmap
        ↓
Выбрать интересную точку
        ↓
Получить score
        ↓
Понять причины score
        ↓
Проверить школы / сады / медицину
        ↓
Проверить метро / транспорт / дороги
        ↓
Проверить природу / воду / шум
        ↓
Рассчитать доступность личных мест
        ↓
Добавить своё наблюдение
        ↓
Сравнить несколько вариантов
```

---

# 100. Итоговый критерий успеха

KARTASPB должен стать не просто картой с маркерами, а персональной пространственной системой принятия решений.

При выборе точки система должна отвечать:

> **«Насколько это место подходит пользователю для жизни, какие факторы дали такой результат, насколько надёжны данные и из каких источников они получены?»**

Минимальный результат анализа точки:

1. общий score;
2. breakdown факторов;
3. completeness;
4. confidence;
5. метро;
6. наземный транспорт;
7. школы;
8. детские сады;
9. государственная медицина;
10. частная медицина;
11. природа;
12. вода;
13. дороги;
14. шум;
15. личные точки и travel time;
16. пользовательские заметки;
17. источники;
18. свежесть данных.

---

# 101. Первая команда AI-агенту после получения этого файла

Если проект находится на ранней стадии, не реализовывай весь документ сразу.

```text
1. Изучи текущий репозиторий KARTASPB.
2. Сопоставь существующий код с этим ТЗ.
3. Не удаляй рабочий код без причины.
4. Определи текущий фактический спринт.
5. Реализуй только ближайший незавершённый этап.
6. После реализации выполни все проверки.
7. Сделай отчёт по формату этого документа.
8. Не переходи к следующему спринту автоматически.
```

---

# 102. Приоритет при конфликте требований

При конфликте требований использовать порядок:

1. текущее прямое указание владельца проекта;
2. этот Master Specification;
3. актуальная architecture documentation;
4. предыдущие технические документы;
5. предположения AI-агента.

Если конфликт касается архитектуры, данных, платного сервиса или смены стека — не принимать скрытое решение. Зафиксировать конфликт и запросить решение владельца проекта.

---

**Конец Master Specification KARTASPB.**
