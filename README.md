# Telegram-бот для аналитики по видео

Проект: Telegram-бот на Python (aiogram) + PostgreSQL для ответов на аналитические вопросы по видео на естественном русском языке.  
Бот принимает текстовый запрос, трансформирует его в структурированное описание метрики (через LLM) и вычисляет значение по данным в БД.

---

## 1. Требования

- Docker и docker-compose
- Либо Python 3.11+ (для локального запуска без Docker)

---

## 2. Структура проекта (основное)

```text
.
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ db.py
│  ├─ main.py
│  ├─ bot/
│  │  ├─ __init__.py
│  │  └─ handlers.py
│  ├─ nlp/
│  │  ├─ __init__.py
│  │  ├─ llm_client.py
│  │  ├─ prompt_builder.py
│  │  └─ query_schema.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ query_builder.py
│  │  ├─ video_service.py
│  │  └─ date_utils.py
│  ├─ migrations/
│  │  └─ 001_create_tables.sql
│  └─ scripts/
│     └─ load_json.py
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
├─ .env.example
└─ README.md
```
JSON-файл с данными (videos) рекомендуется положить в каталог data/videos.json в корне репозитория.

## 3. Настройка окружения
Склонируйте репозиторий.

Скопируйте файл .env.example в .env и заполните значения:

TELEGRAM_BOT_TOKEN — токен бота из @BotFather.

DATABASE_URL — строка подключения к PostgreSQL (по умолчанию подходит для docker-compose).

LLM_API_KEY / LLM_API_BASE / LLM_MODEL — параметры LLM-провайдера.

Скачайте JSON с исходными данными и положите его в data/videos.json.

## 4. Запуск в Docker
### 4.1. Поднять БД и бота

docker-compose up -d --build

После этого:

сервис db — PostgreSQL с базой video_stats;

сервис bot — контейнер с приложением (бот пока не сможет отвечать корректно, т.к. нет таблиц и данных).
### 4.2. Применить SQL-миграции
Файл миграции лежит в app/migrations/001_create_tables.sql и уже смонтирован в контейнер db по пути /app/app/migrations/001_create_tables.sql (см. docker-compose.yml).
Запуск миграции:
```json
docker-compose exec db \
  psql -U video_user -d video_stats \
  -f /app/app/migrations/001_create_tables.sql
  ```
### 4.3. Загрузить JSON-данные в БД
Скрипт загрузки: app/scripts/load_json.py.
Предполагается, что файл с данными лежит в data/videos.json внутри репозитория (он был скопирован в образ при сборке).
Запуск скрипта внутри контейнера bot:
```json
docker-compose exec bot \
  python -m app.scripts.load_json /app/data/videos.json
  ```
Скрипт:
читает JSON;
создаёт записи в таблице videos;
создаёт записи в таблице video_snapshots.
После успешной загрузки БД готова к работе, а бот может отвечать на запросы.

## 5. Локальный запуск без Docker
Установите PostgreSQL локально, создайте базу:
createdb video_stats

Примените миграцию:
psql -d video_stats -f app/migrations/001_create_tables.sql

Установите зависимости:
pip install -r requirements.txt

Скопируйте .env.example в .env и настройте:
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/video_stats
остальные переменные по аналогии.

Загрузите JSON:
python -m app.scripts.load_json data/videos.json

Запустите бота:
python -m app.main
## 6. Архитектура приложения
### 6.1. Слой конфигурации
app/config.py
Читает переменные окружения (TELEGRAM_BOT_TOKEN, DATABASE_URL, LLM_API_KEY, LLM_API_BASE, LLM_MODEL) через pydantic.
Предоставляет глобальный объект settings.
app/db.py
Создаёт SQLAlchemy engine и SessionLocal.
Функция get_session() возвращает сессию для работы с БД.
6.2. Схема БД
SQL-миграция app/migrations/001_create_tables.sql создаёт две таблицы:
videos — итоговая статистика по ролику:
id (PK),
creator_id,
video_created_at,
views_count, likes_count, comments_count, reports_count,
created_at, updated_at.
video_snapshots — почасовые замеры:
id (PK),
video_id (FK → videos.id),
views_count, likes_count, comments_count, reports_count,
delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count,
created_at, updated_at.
Добавлены индексы по creator_id + video_created_at и по created_at/video_id для ускорения типичных аналитических запросов.
6.3. Загрузка данных
app/scripts/load_json.py
Cкрипт читает JSON (массив объектов videos с вложенными snapshots) и записывает данные в таблицы videos и video_snapshots. Выполняет вставку через SQLAlchemy Core или сырой SQL с INSERT ... ON CONFLICT DO NOTHING, чтобы избежать дублирования при повторном запуске.
## 7. Telegram-бот (aiogram)
app/main.py
Точка входа.
Создаёт Bot и Dispatcher, регистрирует хендлеры из app.bot.handlers и запускает dp.start_polling(bot).
app/bot/handlers.py
Обработчик текстовых сообщений:
Принимает текст запроса на русском.
Передаёт его в NLU-слой (app.nlp.llm_client.parse_user_query).
Получает структурированное описание метрики.
Передаёт описание в сервисный слой (app.services.video_service.execute_analytics_query).
Возвращает пользователю одно число (в виде строки).
Контекст диалога не хранится: каждый запрос обрабатывается независимо.
## 8. Подход NL → SQL (через структурированный запрос)
Главная идея: LLM не генерирует SQL, а возвращает строго типизированный JSON, описывающий задачу. Далее этот JSON конвертируется в SQL локально, детерминированным и проверяемым кодом.
8.1. Схема структурированного запроса
app/nlp/query_schema.py
Определяет Pydantic-модели, например:
DateRange:
start: Optional[str] — ISO-строка начала периода;
end: Optional[str] — ISO-строка конца (включительно).
ParsedQuery:
metric — тип агрегата ("videos_count", "sum_views_delta", "sum_views_total", "sum_likes_total" и т.п.);
entity — уровень ("video" или "snapshot");
фильтры: creator_id, min_views, date_range;
спец-флаг special, например "distinct_videos_with_positive_delta" для вопросов вида «Сколько разных видео получали новые просмотры ...».
LLM обязан вернуть JSON, который валидируется через ParsedQuery. Любой невалидный ответ приведёт к ошибке, а не к выполнению «сомнительного» SQL.
8.2. Промпт и описание схемы данных
app/nlp/prompt_builder.py
Формирует промпт для LLM:
описывает таблицы videos и video_snapshots, их поля и смысл;
объясняет, какие бывают типы метрик и фильтров;
даёт примеры (русский вопрос → JSON ParsedQuery);
жёстко требует вернуть только JSON без комментариев и текста.
app/nlp/llm_client.py
Отправляет промпт в LLM (например, OpenAI gpt-4.1-mini), получает ответ, парсит JSON и валидирует его в ParsedQuery.
8.3. Преобразование JSON → SQL
app/services/query_builder.py
На вход получает ParsedQuery, на выходе — строку SQL и словарь параметров.
Примеры:

«Сколько всего видео есть в системе?»
→ SELECT COUNT(*) FROM videos;
«Сколько видео у креатора с id X вышло с 1 по 5 ноября 2025 включительно?»
→ SELECT COUNT(*) FROM videos WHERE creator_id = :creator_id AND video_created_at BETWEEN :start AND :end;
«Сколько видео набрало больше 100 000 просмотров за всё время?»
→ SELECT COUNT(*) FROM videos WHERE views_count > :min_views;
«На сколько просмотров в сумме выросли все видео 28 ноября 2025?»
→ SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at::date = :date;
«Сколько разных видео получали новые просмотры 27 ноября 2025?»
→ SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE created_at::date = :date AND delta_views_count > 0;
app/services/video_service.py
Использует query_builder и SQLAlchemy для выполнения запроса и возвращает одно целое число (0 по умолчанию, если результат NULL).
## 9. Проверка через служебного бота
После того как:
БД поднята и миграции применены;
данные из JSON загружены;
Telegram-бот запущен и доступен;
можно запустить проверку:
/check @yourbotnickname https://github.com/yourrepo
в чате с @rlt_test_checker_bot, где:
@yourbotnickname — ник вашего Telegram-бота;
https://github.com/yourrepo — URL публичного репозитория с этим кодом.
Служебный бот прогонит набор запросов и сравнит ответы с эталонными значениями.

---