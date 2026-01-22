# MPCabinet Ecosystem - Архитектура многоботовой системы

**Версия документа:** 1.0
**Дата создания:** 22.01.2026
**Для версии Picture Bot:** 0.5.0

---

## Содержание

1. [Введение](#1-введение)
2. [Архитектура общей инфраструктуры](#2-архитектура-общей-инфраструктуры)
3. [Shared библиотека компонентов](#3-shared-библиотека-компонентов)
4. [Создание нового бота](#4-создание-нового-бота)
5. [Деплой на VPS](#5-деплой-на-vps)
6. [Примеры для разных типов ботов](#6-примеры-для-разных-типов-ботов)
7. [База данных: детали](#7-база-данных-детали)
8. [Переменные окружения](#8-переменные-окружения)
9. [Лучшие практики](#9-лучшие-практики)
10. [Troubleshooting](#10-troubleshooting)
11. [Приложения](#11-приложения)

---

## 1. Введение

### Что такое MPCabinet Ecosystem?

MPCabinet Ecosystem - это архитектура для создания нескольких Telegram ботов, которые:

- **Живут в отдельных Git-репозиториях** (независимая разработка и деплой)
- **Используют общую PostgreSQL базу данных** (единая идентификация пользователей)
- **Переиспользуют готовые компоненты** (аналитика, уведомления, middleware)
- **Работают на одном VPS** (экономия ресурсов, простая инфраструктура)

### Зачем нужна общая БД?

**Идентификация пользователя:** `telegram_id` (BIGINT) - глобальный идентификатор для всех ботов. Если пользователь взаимодействовал с ботом A, вы видите его историю при обращении к боту B.

**Общая аналитика:** Все события (user_start, errors, специфичные действия) записываются в `shared.analytics_events`. Вы получаете объединенную статистику по всей экосистеме.

**Уведомления и дайджесты:** Один Telegram-канал для мониторинга всех ботов. Ежедневные дайджесты показывают активность по каждому боту.

### Преимущества архитектуры

✅ **Независимая разработка**: Каждый бот - отдельный репозиторий
✅ **Переиспользование кода**: Copy-paste готовых компонентов
✅ **Единая аналитика**: Все пользователи и события в одной БД
✅ **Graceful degradation**: Боты работают даже без БД
✅ **Простой деплой**: Docker Compose на одном VPS
✅ **Масштабируемость**: Легко добавлять новые боты

### Архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────────┐
│                         VPS Server                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Docker Compose Network                  │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Bot A      │  │  Bot B      │  │  Bot C      │  │   │
│  │  │ (Picture)   │  │  (CRM)      │  │  (API)      │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │   │
│  │         │                │                │         │   │
│  │         └────────────────┼────────────────┘         │   │
│  │                          │                          │   │
│  │                   ┌──────▼──────┐                   │   │
│  │                   │ PostgreSQL  │                   │   │
│  │                   │   (shared   │                   │   │
│  │                   │    schema)  │                   │   │
│  │                   └─────────────┘                   │   │
│  │                                                       │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │   Local Telegram Bot API Server (optional)   │   │   │
│  │  │         (для файлов > 50MB)                  │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │
                   Telegram Users
```

---

## 2. Архитектура общей инфраструктуры

### 2.1 PostgreSQL с shared схемой

#### Основные таблицы

**`shared.users`** - глобальный реестр пользователей
- `telegram_id BIGINT PRIMARY KEY` - уникальный ID пользователя
- `username TEXT` - @username (может быть NULL)
- `first_name TEXT` - имя
- `last_name TEXT` - фамилия
- `language_code TEXT` - код языка (ru, en)
- `first_seen TIMESTAMPTZ` - первое обращение к любому боту
- `last_seen TIMESTAMPTZ` - последнее обращение

**`shared.analytics_events`** - все события из всех ботов
- `id BIGSERIAL PRIMARY KEY`
- `telegram_id BIGINT` → ссылка на `shared.users`
- `bot_name TEXT` - имя бота (например: "Picture Bot", "CRM Bot")
- `event_type TEXT` - тип события (user_start, article_request, error, ...)
- `event_data JSONB` - дополнительные данные события
- `created_at TIMESTAMPTZ` - время события

#### Индексы для производительности

```sql
-- Быстрый поиск по пользователю
CREATE INDEX idx_analytics_telegram_id ON shared.analytics_events(telegram_id);

-- Фильтрация по боту и типу события
CREATE INDEX idx_analytics_bot_event ON shared.analytics_events(bot_name, event_type);

-- Статистика за период
CREATE INDEX idx_analytics_created_at ON shared.analytics_events(created_at DESC);
```

#### SQL миграция

Миграция находится в `ecosystem_shared/sql/02-analytics.sql` и автоматически выполняется при первом запуске PostgreSQL контейнера (см. [Приложение B](#приложение-b-sql-скрипт-создания-shared-схемы)).

### 2.2 Docker Compose на VPS

#### Структура сервисов

**telegram-bot-api** (опционально, для медиа-ботов):
- Образ: `aiogram/telegram-bot-api:latest`
- Порты: 8081 (API), 8082 (stats)
- Лимит файлов: 2GB (vs стандартные 50MB)
- Volume: `/var/lib/telegram-bot-api` для локального хранилища

**postgres**:
- Образ: `postgres:16-alpine`
- Порт: 5432
- Volume: `/var/lib/postgresql/data` для persistent storage
- Схемы: `shared` (общая) + бот-специфичные (опционально)

**bot-picture**, **bot-crm**, **bot-***: (ваши боты)
- Custom Dockerfile для каждого бота
- Автоматический restart при падении
- Доступ к `postgres` и `telegram-bot-api` через Docker сеть

#### Порты и сети

Все сервисы работают в одной Docker сети `telegram-network`. Боты обращаются к БД и API по именам контейнеров:

```env
DATABASE_URL=postgresql://telegram_admin:pass@postgres:5432/telegram_ecosystem
TELEGRAM_API_BASE_URL=http://telegram-bot-api:8081
```

#### Persistent storage

Критические volumes:
- `postgres_data:/var/lib/postgresql/data` - данные БД
- `telegram_bot_api_data:/var/lib/telegram-bot-api` - медиа файлы (если используется)

⚠️ **Важно:** Настройте автобэкапы для `postgres_data`!

#### Масштабирование

**Конфигурация VPS:**

| Параметр | 1-2 бота | 3-5 ботов | 6-10 ботов |
|----------|----------|-----------|------------|
| RAM | 2 GB | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores | 6 cores |
| Disk | 20 GB SSD | 40 GB SSD | 80 GB SSD |
| PostgreSQL pool | max=10 | max=20 | max=50 |

**Рекомендация:** Начните с 2 GB RAM и увеличивайте по необходимости.

### 2.3 Local Telegram Bot API Server

#### Зачем нужен?

**Используйте Local Bot API если:**
- ✅ Ваш бот отправляет файлы > 50MB (видео, архивы)
- ✅ Нужно локальное хранилище медиа (экономия трафика)
- ✅ Требуется работа без интернета (редкий случай)

**НЕ используйте если:**
- ❌ Бот только текстовый
- ❌ Файлы всегда < 50MB
- ❌ Хотите минимизировать использование ресурсов

#### Конфигурация

В `.env`:
```env
TELEGRAM_API_BASE_URL=http://telegram-bot-api:8081
TELEGRAM_API_LOCAL=true
```

В `docker-compose.yml`:
```yaml
services:
  telegram-bot-api:
    image: aiogram/telegram-bot-api:latest
    environment:
      TELEGRAM_API_ID: "ваш_api_id"
      TELEGRAM_API_HASH: "ваш_api_hash"
    ports:
      - "8081:8081"
    volumes:
      - telegram_bot_api_data:/var/lib/telegram-bot-api
```

Получить API_ID и API_HASH: https://my.telegram.org/apps

---

## 3. Shared библиотека компонентов

### 3.1 Структура папки ecosystem_shared/

```
ecosystem_shared/
├── README.md                    # Как использовать эти компоненты
├── db/
│   ├── __init__.py
│   └── connection.py           # Пул PostgreSQL (94 строки)
├── services/
│   ├── __init__.py
│   ├── analytics.py            # Аналитика (370 строк)
│   ├── notifications.py        # Уведомления (134 строки)
│   └── digest.py               # Дайджесты (57 строк)
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Логирование
│   ├── decorators.py           # Декораторы (timing, retry, logging)
│   └── exceptions.py           # Base exceptions
├── bot/
│   └── middlewares/
│       ├── __init__.py
│       ├── rate_limiter.py     # Rate limiter (защита от спама)
│       └── error_handler.py    # Error handler (глобальная обработка ошибок)
├── config/
│   ├── __init__.py
│   └── base_settings.py        # BaseSettings класс
├── sql/
│   └── 02-analytics.sql        # SQL миграция для shared схемы
└── templates/
    ├── main.py.template         # Шаблон main.py
    ├── .env.template            # Шаблон .env
    └── requirements.txt         # Базовые зависимости
```

### 3.2 Компоненты (детальное описание)

#### db/connection.py

**Назначение:** Singleton пул соединений PostgreSQL через asyncpg.

**API:**
- `get_pool() -> Optional[asyncpg.Pool]` - получить пул (создаёт если нужно)
- `close_pool() -> None` - закрыть пул (graceful shutdown)

**Graceful degradation:**
Если `DATABASE_URL` не настроен или БД недоступна - возвращает `None`. Бот продолжает работу без аналитики.

**Пример использования:**
```python
from db.connection import get_pool, close_pool

# В main.py
pool = await get_pool()
if pool:
    logger.info("✅ PostgreSQL pool initialized")
else:
    logger.warning("⚠️  Analytics disabled")

# При завершении
await close_pool()
```

---

#### services/analytics.py

**Назначение:** Система аналитики для отслеживания пользователей и событий.

**Класс `AnalyticsService`:**

**Методы для трекинга событий:**

1. `track_user_start(telegram_id, username, first_name, last_name, language_code, bot_name)`
   - Регистрирует нового пользователя или обновляет last_seen
   - **Обязательно вызывать в /start handler!**

2. `track_event(telegram_id, bot_name, event_type, event_data=None)`
   - Универсальный метод для любых событий
   - `event_data` - JSONB объект с дополнительными данными

3. `track_photos_sent(telegram_id, bot_name, count, success_callback=None)`
   - Специфичный метод для медиа-ботов
   - Callback вызывается после успешной отправки фото

4. `track_video_sent(telegram_id, bot_name, success_callback=None)`
   - Для отправки видео
   - Использует callback pattern

5. `track_error(telegram_id, bot_name, error_message)`
   - Логирование ошибок в БД

6. `get_daily_stats(bot_name=None) -> Dict`
   - Получить статистику за последние 24 часа
   - Если `bot_name=None` - статистика по всем ботам

**Пример использования:**
```python
from services.analytics import AnalyticsService

analytics = AnalyticsService()

# В /start handler
@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await analytics.track_user_start(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        bot_name="Your Bot Name"
    )
    await message.answer("Привет!")

# Трекинг специфичного события
await analytics.track_event(
    telegram_id=user.id,
    bot_name="Your Bot Name",
    event_type="button_clicked",
    event_data={"button": "settings"}
)

# Callback pattern для медиа
async def on_photo_sent():
    await analytics.track_photos_sent(
        telegram_id=user.id,
        bot_name="Your Bot Name",
        count=5
    )

await bot.send_media_group(chat_id, photos)
await on_photo_sent()  # После успешной отправки
```

---

#### services/notifications.py

**Назначение:** Отправка уведомлений в Telegram-канал.

**Функции:**

1. `send_new_user_notification(bot, telegram_id, username, first_name, bot_name)`
   - Мгновенное уведомление о новом пользователе
   - Формат: "🆕 Новый пользователь в [Bot Name]: @username (ID: 12345)"

2. `send_daily_digest(bot, stats)`
   - Отправка ежедневного дайджеста
   - `stats` - словарь со статистикой (из `get_daily_stats()`)

**Требования:**
- `ANALYTICS_CHANNEL_ID` должен быть настроен в `.env`
- Бот должен быть администратором канала

**Пример:**
```python
from services.notifications import send_new_user_notification

# В /start handler после track_user_start
await send_new_user_notification(
    bot=bot,
    telegram_id=user.id,
    username=user.username,
    first_name=user.first_name,
    bot_name="Your Bot Name"
)
```

---

#### services/digest.py

**Назначение:** Автоматическая отправка ежедневного дайджеста (для APScheduler).

**Функция:**
- `send_daily_digest_job(bot)` - джоб для планировщика

**Интеграция с APScheduler:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.digest import send_daily_digest_job
import pytz

msk_tz = pytz.timezone('Europe/Moscow')
scheduler = AsyncIOScheduler(timezone=msk_tz)

scheduler.add_job(
    send_daily_digest_job,
    trigger=CronTrigger(hour=0, minute=0, timezone=msk_tz),
    args=[bot],
    id='daily_digest',
    name='Daily Analytics Digest'
)

scheduler.start()
```

---

#### bot/middlewares/rate_limiter.py

**Назначение:** Защита от спама (rate limiting).

**Параметры:**
- `RATE_LIMIT_SECONDS` (из settings) - минимальный интервал между запросами

**Поведение:**
- Если пользователь отправляет запросы слишком часто - отправляется предупреждение
- Запрос не обрабатывается

**Регистрация:**
```python
from bot.middlewares.rate_limiter import RateLimiterMiddleware

dp.message.middleware(RateLimiterMiddleware())
```

---

#### bot/middlewares/error_handler.py

**Назначение:** Глобальная обработка ошибок.

**Функции:**
- Логирует все необработанные исключения
- Отправляет пользователю красивое сообщение об ошибке
- Опционально: трекает ошибку в аналитику

**Регистрация:**
```python
from bot.middlewares.error_handler import ErrorHandlerMiddleware

dp.message.middleware(ErrorHandlerMiddleware())
dp.callback_query.middleware(ErrorHandlerMiddleware())
```

---

#### config/base_settings.py

**Назначение:** Базовый класс конфигурации для всех ботов.

**Базовые поля:**
- `BOT_TOKEN: str` - обязательно
- `LOG_LEVEL: str = "INFO"`
- `DATABASE_URL: Optional[str] = None`
- `ENABLE_ANALYTICS: bool = True`
- `ANALYTICS_CHANNEL_ID: Optional[int] = None`
- `RATE_LIMIT_SECONDS: float = 3.0`
- `TELEGRAM_API_BASE_URL: Optional[str] = None`
- `TELEGRAM_API_LOCAL: bool = False`

**Как использовать:**
```python
# config/settings.py в вашем боте
from config.base_settings import BaseSettings

class Settings(BaseSettings):
    # Добавьте специфичные для бота настройки
    YOUR_API_KEY: str
    YOUR_BOT_SETTING: int = 42

settings = Settings()
```

---

## 4. Создание нового бота

### 4.1 Подготовка

#### Шаг 1: Создайте репозиторий

```bash
# Создайте новый репозиторий на GitHub
# Клонируйте локально
git clone https://github.com/your-username/your-new-bot.git
cd your-new-bot
```

#### Шаг 2: Структура проекта

Рекомендуемая структура:

```
your-new-bot/
├── .env                  # Переменные окружения (НЕ коммитить!)
├── .gitignore
├── requirements.txt
├── Dockerfile            # Для деплоя
├── main.py               # Точка входа
├── config/
│   ├── __init__.py
│   └── settings.py       # Настройки (наследуется от BaseSettings)
├── bot/
│   ├── __init__.py
│   ├── handlers/         # Ваши handlers
│   └── middlewares/      # Shared middlewares (копируются)
├── db/                   # Shared компонент
├── services/             # Shared компоненты
└── utils/                # Shared компоненты
```

#### Шаг 3: Скопируйте ecosystem_shared/

```bash
# Из Picture Bot репозитория
cp -r ../MPCabinet_Picture_Bot/ecosystem_shared/* ./

# Или вручную скопируйте папки:
# - db/
# - services/
# - utils/
# - bot/middlewares/
# - config/base_settings.py
# - sql/02-analytics.sql
```

### 4.2 Интеграция shared компонентов

#### Создайте config/settings.py

```python
from config.base_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки вашего бота."""

    # Добавьте специфичные для бота настройки
    # Например:
    # API_KEY: str
    # MAX_REQUESTS_PER_MINUTE: int = 60

    pass  # Если нет дополнительных настроек

settings = Settings()
```

#### Создайте main.py

Используйте шаблон из `ecosystem_shared/templates/main.py.template`:

```bash
cp ecosystem_shared/templates/main.py.template main.py
```

Отредактируйте `main.py`:
1. Импортируйте ваши handlers
2. Зарегистрируйте роутеры
3. Добавьте бот-специфичную логику

#### Создайте requirements.txt

Начните с базовых зависимостей:

```bash
cp ecosystem_shared/templates/requirements.txt requirements.txt
```

Добавьте специфичные для бота зависимости:

```txt
# Базовые зависимости (из ecosystem_shared)
aiogram>=3.13.0
python-dotenv>=1.0.0
pydantic>=2.4.0
pydantic-settings>=2.5.0
asyncpg>=0.29.0
apscheduler>=3.10.0
pytz>=2024.1

# Ваши специфичные зависимости
aiohttp>=3.9.0              # Для HTTP запросов
pillow>=10.0.0              # Для обработки изображений
redis>=5.0.0                # Для кеширования
```

### 4.3 Интеграция аналитики

#### В /start handler

```python
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from services.analytics import AnalyticsService
from services.notifications import send_new_user_notification

router = Router()
analytics = AnalyticsService()

BOT_NAME = "Your Bot Name"  # Уникальное имя бота

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user

    # 1. Трекинг пользователя
    await analytics.track_user_start(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        bot_name=BOT_NAME
    )

    # 2. Уведомление в канал (опционально, для новых пользователей)
    # Проверка на нового пользователя реализована в track_user_start
    await send_new_user_notification(
        bot=message.bot,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        bot_name=BOT_NAME
    )

    # 3. Ответ пользователю
    await message.answer("Привет! Я готов помочь.")
```

#### В других handlers

```python
from services.analytics import AnalyticsService

analytics = AnalyticsService()

@router.message()
async def some_feature_handler(message: Message):
    # Трекинг события
    await analytics.track_event(
        telegram_id=message.from_user.id,
        bot_name=BOT_NAME,
        event_type="feature_used",
        event_data={"feature": "some_feature", "input": message.text}
    )

    # Ваша логика
    await message.answer("Обработано!")
```

#### Callback pattern для медиа

```python
# Для фото
async def on_photos_sent():
    await analytics.track_photos_sent(
        telegram_id=user_id,
        bot_name=BOT_NAME,
        count=len(photos)
    )

await bot.send_media_group(chat_id, photos)
await on_photos_sent()

# Для видео
async def on_video_sent():
    await analytics.track_video_sent(
        telegram_id=user_id,
        bot_name=BOT_NAME
    )

await bot.send_video(chat_id, video)
await on_video_sent()
```

### 4.4 Настройка middleware

В `main.py`:

```python
from bot.middlewares.rate_limiter import RateLimiterMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware

# В async def main()
dp = Dispatcher()

# Порядок важен! Rate limiter должен быть первым
dp.message.middleware(RateLimiterMiddleware())
dp.message.middleware(ErrorHandlerMiddleware())
dp.callback_query.middleware(ErrorHandlerMiddleware())
```

### 4.5 Создайте .env файл

```bash
cp ecosystem_shared/templates/.env.template .env
```

Заполните обязательные переменные:

```env
BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=postgresql://telegram_admin:password@postgres:5432/telegram_ecosystem
ANALYTICS_CHANNEL_ID=-1001234567890
ENABLE_ANALYTICS=true
```

⚠️ **Не забудьте добавить .env в .gitignore!**

---

## 5. Деплой на VPS

### 5.1 Подготовка окружения

#### Структура папок на VPS

```
/opt/telegram-ecosystem/
├── docker-compose.yml       # Главный файл
├── .env                     # Общие переменные (пароли БД, API tokens)
├── postgres/
│   └── init/
│       └── 02-analytics.sql # Автоматическая миграция
├── bot-picture/
│   ├── Dockerfile
│   ├── .env
│   └── ... (код бота)
├── bot-crm/
│   ├── Dockerfile
│   ├── .env
│   └── ... (код бота)
└── bot-your-new-bot/
    ├── Dockerfile
    ├── .env
    └── ... (код бота)
```

#### Создайте .env файл на VPS

```bash
cd /opt/telegram-ecosystem
nano .env
```

Содержимое:

```env
# PostgreSQL
POSTGRES_USER=telegram_admin
POSTGRES_PASSWORD=ваш_сильный_пароль
POSTGRES_DB=telegram_ecosystem

# Local Bot API (если используется)
TELEGRAM_API_ID=ваш_api_id
TELEGRAM_API_HASH=ваш_api_hash
```

### 5.2 Миграции БД

#### Автоматическое создание shared схемы

При первом запуске PostgreSQL контейнера:

1. Скопируйте `ecosystem_shared/sql/02-analytics.sql` в `/opt/telegram-ecosystem/postgres/init/`
2. PostgreSQL автоматически выполнит все `.sql` файлы из этой папки

```bash
mkdir -p /opt/telegram-ecosystem/postgres/init
cp ecosystem_shared/sql/02-analytics.sql /opt/telegram-ecosystem/postgres/init/
```

#### Проверка подключения

```bash
# Подключитесь к PostgreSQL контейнеру
docker exec -it telegram_ecosystem_postgres psql -U telegram_admin -d telegram_ecosystem

# Проверьте схему
\dn

# Проверьте таблицы
\dt shared.*

# Выход
\q
```

### 5.3 Docker Compose для нового бота

#### Создайте Dockerfile для вашего бота

```dockerfile
FROM python:3.11-slim

# Установка зависимостей системы (если нужно)
# Например, для ffmpeg (медиа-боты):
# RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY . .

# Запуск бота
CMD ["python", "main.py"]
```

#### Добавьте сервис в docker-compose.yml

```yaml
version: '3.8'

services:
  # ... существующие сервисы (postgres, telegram-bot-api, другие боты)

  bot-your-new-bot:
    build: ./bot-your-new-bot
    container_name: telegram_ecosystem_bot_your_new_bot
    restart: unless-stopped
    env_file:
      - ./bot-your-new-bot/.env
    depends_on:
      - postgres
      # - telegram-bot-api  # Если используете Local Bot API
    networks:
      - telegram-network
    volumes:
      - ./bot-your-new-bot:/app  # Для разработки (опционально)

networks:
  telegram-network:
    driver: bridge

volumes:
  postgres_data:
  # telegram_bot_api_data:  # Если используете Local Bot API
```

#### Запуск

```bash
cd /opt/telegram-ecosystem

# Сборка и запуск нового бота
docker compose up -d --build bot-your-new-bot

# Проверка логов
docker compose logs -f bot-your-new-bot
```

---

## 6. Примеры для разных типов ботов

### 6.1 Медиа-бот (как Picture Bot)

**Особенности:**
- Отправка фото/видео > 50MB
- Использование Local Bot API
- HLS конвертация (если нужна)

**Дополнительные зависимости:**
```txt
aiohttp>=3.9.0              # HTTP клиент для загрузки
pillow>=10.0.0              # Обработка изображений
ffmpeg-python>=0.2.0        # Работа с видео (опционально)
```

**Dockerfile с ffmpeg:**
```dockerfile
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**.env настройки:**
```env
TELEGRAM_API_BASE_URL=http://telegram-bot-api:8081
TELEGRAM_API_LOCAL=true
```

**Пример handler:**
```python
from services.analytics import AnalyticsService

analytics = AnalyticsService()

@router.message()
async def send_media_handler(message: Message):
    user_id = message.from_user.id

    # Загрузка и отправка медиа
    photos = await download_photos()
    await bot.send_media_group(message.chat.id, photos)

    # Трекинг после успешной отправки
    await analytics.track_photos_sent(
        telegram_id=user_id,
        bot_name="Media Bot",
        count=len(photos)
    )
```

### 6.2 Текстовый бот

**Особенности:**
- Минимальная конфигурация
- Стандартный Telegram API (без Local)
- Только аналитика + middleware

**Дополнительные зависимости:**
Только базовые из `ecosystem_shared/templates/requirements.txt`

**.env настройки:**
```env
BOT_TOKEN=your_token
DATABASE_URL=postgresql://telegram_admin:pass@postgres:5432/telegram_ecosystem
ANALYTICS_CHANNEL_ID=-1001234567890
ENABLE_ANALYTICS=true
TELEGRAM_API_BASE_URL=  # Пусто - используем стандартный API
TELEGRAM_API_LOCAL=false
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**Пример handler:**
```python
from services.analytics import AnalyticsService

analytics = AnalyticsService()

@router.message(F.text.startswith("/command"))
async def command_handler(message: Message):
    user_id = message.from_user.id

    # Трекинг события
    await analytics.track_event(
        telegram_id=user_id,
        bot_name="Text Bot",
        event_type="command_used",
        event_data={"command": message.text}
    )

    await message.answer("Команда обработана!")
```

### 6.3 CRM/управление пользователями

**Особенности:**
- Расширенная аналитика (новые event_type)
- Дополнительные таблицы в специфичной схеме
- Связь с `shared.users` через `telegram_id`

**Создайте бот-специфичную схему:**

```sql
-- postgres/init/03-crm-schema.sql
CREATE SCHEMA IF NOT EXISTS crm;

-- Дополнительные данные пользователей
CREATE TABLE IF NOT EXISTS crm.user_profiles (
    telegram_id BIGINT PRIMARY KEY REFERENCES shared.users(telegram_id),
    subscription_status TEXT DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    total_purchases DECIMAL(10, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Заказы
CREATE TABLE IF NOT EXISTS crm.orders (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES shared.users(telegram_id),
    product_name TEXT,
    amount DECIMAL(10, 2),
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Пример использования:**

```python
from db.connection import get_pool
from services.analytics import AnalyticsService

analytics = AnalyticsService()

@router.message(F.text == "/subscribe")
async def subscribe_handler(message: Message):
    user_id = message.from_user.id
    pool = await get_pool()

    if pool:
        async with pool.acquire() as conn:
            # Обновление в CRM-специфичной схеме
            await conn.execute("""
                INSERT INTO crm.user_profiles (telegram_id, subscription_status)
                VALUES ($1, 'premium')
                ON CONFLICT (telegram_id) DO UPDATE
                SET subscription_status = 'premium',
                    subscription_expires_at = NOW() + INTERVAL '30 days'
            """, user_id)

    # Трекинг в общей аналитике
    await analytics.track_event(
        telegram_id=user_id,
        bot_name="CRM Bot",
        event_type="subscription_purchased",
        event_data={"plan": "premium", "duration": "30 days"}
    )

    await message.answer("Подписка активирована!")
```

### 6.4 Интеграция с внешним API

**Особенности:**
- HTTP клиент (aiohttp)
- Retry механизмы
- Кеширование ответов

**Дополнительные зависимости:**
```txt
aiohttp>=3.9.0
redis>=5.0.0                # Для кеширования
```

**Пример HTTP клиента с retry:**

```python
import aiohttp
from utils.decorators import retry

@retry(max_attempts=3, delay=1.0)
async def fetch_data_from_api(api_key: str, user_id: int):
    """Получить данные из внешнего API с retry."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.example.com/data/{user_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            response.raise_for_status()
            return await response.json()

# В handler
@router.message(F.text == "/getdata")
async def get_data_handler(message: Message):
    user_id = message.from_user.id

    try:
        data = await fetch_data_from_api(settings.API_KEY, user_id)

        # Трекинг успешного запроса
        await analytics.track_event(
            telegram_id=user_id,
            bot_name="API Bot",
            event_type="api_request_success",
            event_data={"endpoint": "/data"}
        )

        await message.answer(f"Данные: {data}")

    except Exception as e:
        # Трекинг ошибки
        await analytics.track_error(
            telegram_id=user_id,
            bot_name="API Bot",
            error_message=str(e)
        )

        await message.answer("Ошибка при получении данных")
```

---

## 7. База данных: детали

### 7.1 Таблицы shared схемы

#### shared.users

```sql
CREATE TABLE IF NOT EXISTS shared.users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    language_code TEXT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);
```

**Поля:**
- `telegram_id` - уникальный ID пользователя Telegram (может быть отрицательным для групп)
- `username` - @username (может быть NULL, если пользователь его не установил)
- `first_name` - имя (обязательно)
- `last_name` - фамилия (может быть NULL)
- `language_code` - код языка интерфейса Telegram (ru, en, etc.)
- `first_seen` - когда пользователь впервые обратился к любому боту экосистемы
- `last_seen` - последнее обращение к любому боту

#### shared.analytics_events

```sql
CREATE TABLE IF NOT EXISTS shared.analytics_events (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES shared.users(telegram_id) ON DELETE SET NULL,
    bot_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Поля:**
- `id` - автоинкрементный ID события
- `telegram_id` - ссылка на пользователя (может быть NULL если пользователь удалён)
- `bot_name` - имя бота (например: "Picture Bot", "CRM Bot")
- `event_type` - тип события (см. следующую секцию)
- `event_data` - JSONB с дополнительными данными
- `created_at` - время события

**Индексы:**
```sql
CREATE INDEX idx_analytics_telegram_id ON shared.analytics_events(telegram_id);
CREATE INDEX idx_analytics_bot_event ON shared.analytics_events(bot_name, event_type);
CREATE INDEX idx_analytics_created_at ON shared.analytics_events(created_at DESC);
```

### 7.2 Event types в аналитике

#### Стандартные event_type (для всех ботов)

| event_type | Описание | event_data пример |
|------------|----------|-------------------|
| `user_start` | Пользователь запустил бота (/start) | `null` |
| `error` | Произошла ошибка | `{"error": "Connection timeout"}` |

#### Бот-специфичные event_type

**Picture Bot:**
- `article_request` - запрошен артикул WB
  ```json
  {"nm_id": 12345678}
  ```
- `photo_sent` - отправлены фото
  ```json
  {"count": 5, "nm_id": 12345678}
  ```
- `video_sent` - отправлено видео
  ```json
  {"nm_id": 12345678}
  ```

**Ваши event_type:**

Создавайте собственные типы событий для вашего бота:

```python
# Пример для CRM бота
await analytics.track_event(
    telegram_id=user_id,
    bot_name="CRM Bot",
    event_type="subscription_purchased",  # Ваш тип
    event_data={"plan": "premium", "duration": "30 days"}
)

# Пример для API бота
await analytics.track_event(
    telegram_id=user_id,
    bot_name="API Bot",
    event_type="api_request_success",  # Ваш тип
    event_data={"endpoint": "/users", "response_time_ms": 245}
)
```

**Рекомендации:**
- Используйте snake_case для event_type
- Делайте имена описательными: `subscription_purchased` лучше чем `sub_buy`
- Храните полезные метрики в event_data (JSONB поддерживает запросы)

### 7.3 Запросы для аналитики

#### Новые пользователи за период

```sql
SELECT COUNT(*) as new_users
FROM shared.users
WHERE first_seen >= NOW() - INTERVAL '24 hours';
```

#### Самые активные пользователи (по количеству событий)

```sql
SELECT
    u.telegram_id,
    u.username,
    u.first_name,
    COUNT(e.id) as event_count
FROM shared.users u
JOIN shared.analytics_events e ON u.telegram_id = e.telegram_id
WHERE e.created_at >= NOW() - INTERVAL '7 days'
GROUP BY u.telegram_id, u.username, u.first_name
ORDER BY event_count DESC
LIMIT 10;
```

#### События по типам (статистика за день)

```sql
SELECT
    bot_name,
    event_type,
    COUNT(*) as count
FROM shared.analytics_events
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY bot_name, event_type
ORDER BY bot_name, count DESC;
```

#### История конкретного пользователя

```sql
SELECT
    bot_name,
    event_type,
    event_data,
    created_at
FROM shared.analytics_events
WHERE telegram_id = 123456789
ORDER BY created_at DESC
LIMIT 50;
```

#### Аналитика по JSONB (пример для Picture Bot)

```sql
-- Самые популярные артикулы за неделю
SELECT
    event_data->>'nm_id' as nm_id,
    COUNT(*) as requests
FROM shared.analytics_events
WHERE
    event_type = 'article_request' AND
    created_at >= NOW() - INTERVAL '7 days'
GROUP BY event_data->>'nm_id'
ORDER BY requests DESC
LIMIT 20;
```

---

## 8. Переменные окружения

### 8.1 Обязательные для всех ботов

```env
# ============================================================================
# Telegram Bot (ОБЯЗАТЕЛЬНО)
# ============================================================================

BOT_TOKEN=your_bot_token_from_botfather
```

Получить токен: [@BotFather](https://t.me/BotFather) → `/newbot`

```env
# ============================================================================
# Database (ОБЯЗАТЕЛЬНО для аналитики)
# ============================================================================

DATABASE_URL=postgresql://telegram_admin:password@postgres:5432/telegram_ecosystem
```

**Формат:** `postgresql://user:password@host:port/database`

**Для Docker:** host = `postgres` (имя контейнера)
**Для локальной разработки:** host = `localhost`

```env
# ============================================================================
# Analytics (ОБЯЗАТЕЛЬНО для уведомлений)
# ============================================================================

ENABLE_ANALYTICS=true
ANALYTICS_CHANNEL_ID=-1001234567890
```

**Как получить ANALYTICS_CHANNEL_ID:**

1. Создайте приватный канал в Telegram
2. Добавьте вашего бота в канал как администратора
3. Отправьте любое сообщение в канал
4. Откройте в браузере:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. Найдите секцию:
   ```json
   "chat": {"id": -1001234567890, "title": "Your Channel", ...}
   ```
6. Скопируйте значение `id` (обязательно с минусом!)

### 8.2 Для Local Bot API (опционально)

```env
TELEGRAM_API_BASE_URL=http://telegram-bot-api:8081
TELEGRAM_API_LOCAL=true
```

Используйте только если нужны файлы > 50MB.

**Также требуется в docker-compose.yml:**
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

Получить: https://my.telegram.org/apps

### 8.3 Опциональные настройки

```env
# Уровень логирования
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Rate limiting (защита от спама)
RATE_LIMIT_SECONDS=3.0  # Минимальный интервал между запросами
```

### 8.4 Специфичные для каждого бота

**Picture Bot:**
```env
WB_API_TIMEOUT=30
WB_RATE_LIMIT_DELAY=0.01
FFMPEG_PATH=/usr/bin/ffmpeg
HLS_MAX_VIDEO_SIZE_MB=100
```

**CRM Bot (пример):**
```env
PAYMENT_PROVIDER_TOKEN=your_payment_token
ADMIN_USER_IDS=123456789,987654321
MAX_FREE_REQUESTS_PER_DAY=10
```

**API Bot (пример):**
```env
EXTERNAL_API_KEY=your_api_key
EXTERNAL_API_BASE_URL=https://api.example.com
API_REQUEST_TIMEOUT=10
REDIS_URL=redis://localhost:6379/0
```

---

## 9. Лучшие практики

### 9.1 Аналитика

#### ✅ DO

**Всегда вызывайте track_user_start() в /start handler:**
```python
@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await analytics.track_user_start(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        bot_name="Your Bot"
    )
```

**Используйте callback pattern для медиа:**
```python
# Трекайте ПОСЛЕ успешной отправки
await bot.send_photo(chat_id, photo)
await analytics.track_photos_sent(user_id, "Your Bot", 1)
```

**Graceful degradation:**
```python
# Код аналитики уже обрабатывает недоступность БД
# Не нужно оборачивать в try/except
await analytics.track_event(...)  # Безопасно всегда
```

#### ❌ DON'T

**Не трекайте перед отправкой (может не произойти):**
```python
# ❌ ПЛОХО
await analytics.track_photos_sent(user_id, "Bot", 5)
await bot.send_media_group(chat_id, photos)  # Может упасть!
```

**Не дублируйте события:**
```python
# ❌ ПЛОХО - track_user_start уже создаёт событие
await analytics.track_user_start(...)
await analytics.track_event(..., event_type="user_start")
```

### 9.2 Безопасность

#### ✅ DO

**Никогда не коммитьте .env:**
```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

**Используйте сильные пароли для PostgreSQL:**
```env
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

**Ограничивайте доступ к PostgreSQL:**
```yaml
# docker-compose.yml
postgres:
  networks:
    - telegram-network  # Только внутренняя сеть
  # НЕ публикуйте порт 5432 наружу!
```

**Валидация пользовательского ввода:**
```python
from pydantic import BaseModel, Field, ValidationError

class ArticleRequest(BaseModel):
    nm_id: int = Field(gt=0, le=999999999)

@router.message()
async def handle_article(message: Message):
    try:
        data = ArticleRequest(nm_id=int(message.text))
        # Безопасно использовать data.nm_id
    except (ValueError, ValidationError):
        await message.answer("Неверный артикул")
```

#### ❌ DON'T

**Не храните секреты в коде:**
```python
# ❌ ПЛОХО
API_KEY = "sk_live_abc123"

# ✅ ХОРОШО
from config.settings import Settings
settings = Settings()
API_KEY = settings.API_KEY
```

**Не логируйте sensitive данные:**
```python
# ❌ ПЛОХО
logger.info(f"User {user_id} password: {password}")

# ✅ ХОРОШО
logger.info(f"User {user_id} authenticated")
```

### 9.3 Производительность

#### ✅ DO

**Используйте пул соединений:**
```python
# ✅ Правильно - переиспользует соединения
pool = await get_pool()
async with pool.acquire() as conn:
    await conn.execute(...)
```

**Кешируйте часто запрашиваемые данные:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_config_value(key: str) -> str:
    # Дорогая операция
    return load_from_file(key)
```

**Используйте batch операции:**
```python
# ✅ Один запрос
await conn.executemany(
    "INSERT INTO table (a, b) VALUES ($1, $2)",
    [(1, 2), (3, 4), (5, 6)]
)

# ❌ Много запросов
for a, b in values:
    await conn.execute("INSERT INTO table (a, b) VALUES ($1, $2)", a, b)
```

#### ❌ DON'T

**Не создавайте новое соединение каждый раз:**
```python
# ❌ ПЛОХО - медленно и расходует ресурсы
conn = await asyncpg.connect(DATABASE_URL)
await conn.execute(...)
await conn.close()

# ✅ ХОРОШО - используйте пул
pool = await get_pool()
async with pool.acquire() as conn:
    await conn.execute(...)
```

**Не блокируйте event loop синхронными операциями:**
```python
# ❌ ПЛОХО
result = requests.get(url)  # Синхронный requests блокирует

# ✅ ХОРОШО
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        result = await response.text()
```

### 9.4 Мониторинг

#### ✅ DO

**Регулярно проверяйте логи:**
```bash
docker compose logs -f --tail=100 bot-your-bot
```

**Настройте alerts для критических ошибок:**
```python
# В error handler
if isinstance(error, CriticalError):
    await send_alert_to_admin(str(error))
```

**Используйте дайджесты для отслеживания активности:**
- Проверяйте дайджесты каждое утро
- Обращайте внимание на аномалии (резкий рост/падение активности)
- Мониторьте рост количества ошибок

**Следите за ресурсами VPS:**
```bash
# CPU и RAM
docker stats

# Disk space
df -h
```

---

## 10. Troubleshooting

### 10.1 БД недоступна

**Симптомы:**
- Логи: `⚠️ PostgreSQL unavailable - analytics disabled`
- Аналитика не работает
- Дайджесты не приходят

**Диагностика:**

1. **Проверьте DATABASE_URL в .env:**
   ```bash
   cat .env | grep DATABASE_URL
   ```

   Должно быть:
   ```
   DATABASE_URL=postgresql://user:password@postgres:5432/telegram_ecosystem
   ```

2. **Проверьте что PostgreSQL контейнер запущен:**
   ```bash
   docker ps | grep postgres
   ```

   Если не запущен:
   ```bash
   docker compose up -d postgres
   ```

3. **Проверьте сеть Docker:**
   ```bash
   docker network inspect telegram_ecosystem_telegram-network
   ```

   Боты и postgres должны быть в одной сети.

4. **Проверьте логи PostgreSQL:**
   ```bash
   docker compose logs postgres
   ```

5. **Попробуйте подключиться вручную:**
   ```bash
   docker exec -it telegram_ecosystem_postgres psql -U telegram_admin -d telegram_ecosystem
   ```

**Решение:**

- Если контейнер не запущен → перезапустите
- Если сеть неправильная → пересоздайте через `docker compose down && docker compose up -d`
- Если пароль неверный → проверьте переменные окружения

### 10.2 Бот не отвечает

**Симптомы:**
- Бот не реагирует на сообщения
- Команды не работают

**Диагностика:**

1. **Проверьте что контейнер запущен:**
   ```bash
   docker ps | grep bot-your-bot
   ```

2. **Проверьте логи бота:**
   ```bash
   docker compose logs -f bot-your-bot
   ```

   Ищите ошибки:
   - `Unauthorized` → неверный BOT_TOKEN
   - `Connection timeout` → проблемы с сетью
   - `Rate limit exceeded` → слишком много запросов к Telegram API

3. **Проверьте BOT_TOKEN:**
   ```bash
   cat bot-your-bot/.env | grep BOT_TOKEN
   ```

   Проверьте токен через Telegram API:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

   Должно вернуть информацию о боте.

4. **Проверьте Local Bot API (если используете):**
   ```bash
   docker ps | grep telegram-bot-api
   curl http://localhost:8081/status
   ```

**Решение:**

- Неверный токен → обновите BOT_TOKEN в .env и перезапустите
- Rate limit → добавьте задержки между запросами
- Local API недоступен → проверьте что контейнер запущен

### 10.3 Аналитика не работает

**Симптомы:**
- События не записываются в БД
- Дайджесты не приходят
- Уведомления о новых пользователях не отправляются

**Диагностика:**

1. **Проверьте ENABLE_ANALYTICS:**
   ```bash
   cat .env | grep ENABLE_ANALYTICS
   ```

   Должно быть `true`.

2. **Проверьте что БД доступна:**
   ```bash
   docker exec -it telegram_ecosystem_postgres psql -U telegram_admin -d telegram_ecosystem -c "SELECT COUNT(*) FROM shared.analytics_events;"
   ```

3. **Проверьте миграции:**
   ```bash
   docker exec -it telegram_ecosystem_postgres psql -U telegram_admin -d telegram_ecosystem -c "\dt shared.*"
   ```

   Должны быть таблицы: `shared.users`, `shared.analytics_events`

4. **Проверьте permissions:**
   ```bash
   docker exec -it telegram_ecosystem_postgres psql -U telegram_admin -d telegram_ecosystem -c "\dp shared.*"
   ```

**Решение:**

- Миграции не выполнены → скопируйте `02-analytics.sql` в `postgres/init/` и пересоздайте контейнер
- ENABLE_ANALYTICS=false → измените на `true` и перезапустите бота
- БД недоступна → см. [10.1](#101-бд-недоступна)

### 10.4 Дайджесты не приходят

**Симптомы:**
- Ежедневный дайджест не приходит в 00:00 МСК
- Логи показывают что scheduler не запущен

**Диагностика:**

1. **Проверьте ANALYTICS_CHANNEL_ID:**
   ```bash
   cat .env | grep ANALYTICS_CHANNEL_ID
   ```

   Должен быть отрицательный ID канала.

2. **Проверьте что бот администратор канала:**
   - Откройте канал в Telegram
   - Настройки → Администраторы
   - Бот должен быть в списке

3. **Проверьте логи APScheduler:**
   ```bash
   docker compose logs bot-your-bot | grep -i scheduler
   ```

   Должно быть:
   ```
   ✅ APScheduler started: daily digest at 00:00 MSK
   ```

4. **Проверьте время на VPS:**
   ```bash
   docker exec telegram_ecosystem_bot_your_bot date
   ```

**Решение:**

- Неверный ANALYTICS_CHANNEL_ID → получите правильный ID (см. [8.1](#81-обязательные-для-всех-ботов))
- Бот не администратор → добавьте бота в канал как администратора
- Scheduler не запущен → проверьте что БД доступна и ENABLE_ANALYTICS=true
- Неверная timezone → убедитесь что используется `pytz.timezone('Europe/Moscow')`

### 10.5 Rate limit от Telegram

**Симптомы:**
- Ошибки `Too Many Requests: retry after X`
- Бот медленно отвечает

**Решение:**

1. **Добавьте задержки между запросами:**
   ```python
   import asyncio

   for item in items:
       await bot.send_message(chat_id, item)
       await asyncio.sleep(0.05)  # 50ms задержка
   ```

2. **Используйте send_media_group вместо отдельных send_photo:**
   ```python
   # ✅ Один запрос
   await bot.send_media_group(chat_id, [photo1, photo2, photo3])

   # ❌ Три запроса
   await bot.send_photo(chat_id, photo1)
   await bot.send_photo(chat_id, photo2)
   await bot.send_photo(chat_id, photo3)
   ```

3. **Обрабатывайте retry:**
   ```python
   from aiogram.exceptions import TelegramRetryAfter

   try:
       await bot.send_message(chat_id, text)
   except TelegramRetryAfter as e:
       await asyncio.sleep(e.retry_after)
       await bot.send_message(chat_id, text)
   ```

---

## 11. Приложения

### Приложение A: docker-compose.yml для экосистемы

```yaml
version: '3.8'

services:
  # ==========================================================================
  # PostgreSQL - Общая база данных для всех ботов
  # ==========================================================================
  postgres:
    image: postgres:16-alpine
    container_name: telegram_ecosystem_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-telegram_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Укажите POSTGRES_PASSWORD в .env}
      POSTGRES_DB: ${POSTGRES_DB:-telegram_ecosystem}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d  # Автоматические миграции
    networks:
      - telegram-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U telegram_admin -d telegram_ecosystem"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================================================
  # Local Telegram Bot API Server (опционально, для файлов > 50MB)
  # ==========================================================================
  telegram-bot-api:
    image: aiogram/telegram-bot-api:latest
    container_name: telegram_ecosystem_bot_api
    restart: unless-stopped
    environment:
      TELEGRAM_API_ID: ${TELEGRAM_API_ID:?Укажите TELEGRAM_API_ID в .env}
      TELEGRAM_API_HASH: ${TELEGRAM_API_HASH:?Укажите TELEGRAM_API_HASH в .env}
    ports:
      - "8081:8081"  # API
      - "8082:8082"  # Stats
    volumes:
      - telegram_bot_api_data:/var/lib/telegram-bot-api
    networks:
      - telegram-network

  # ==========================================================================
  # Боты
  # ==========================================================================

  bot-picture:
    build: ./bot-picture
    container_name: telegram_ecosystem_bot_picture
    restart: unless-stopped
    env_file:
      - ./bot-picture/.env
    depends_on:
      postgres:
        condition: service_healthy
      telegram-bot-api:
        condition: service_started
    networks:
      - telegram-network
    volumes:
      - ./bot-picture:/app  # Для разработки (удалить в production)

  bot-crm:
    build: ./bot-crm
    container_name: telegram_ecosystem_bot_crm
    restart: unless-stopped
    env_file:
      - ./bot-crm/.env
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - telegram-network

  # Добавьте ваши боты здесь:
  # bot-your-new-bot:
  #   build: ./bot-your-new-bot
  #   container_name: telegram_ecosystem_bot_your_new_bot
  #   restart: unless-stopped
  #   env_file:
  #     - ./bot-your-new-bot/.env
  #   depends_on:
  #     postgres:
  #       condition: service_healthy
  #   networks:
  #     - telegram-network

# ==============================================================================
# Networks
# ==============================================================================
networks:
  telegram-network:
    driver: bridge

# ==============================================================================
# Volumes (persistent storage)
# ==============================================================================
volumes:
  postgres_data:
    driver: local
  telegram_bot_api_data:
    driver: local
```

### Приложение B: SQL скрипт создания shared схемы

См. файл: `ecosystem_shared/sql/02-analytics.sql`

```sql
-- ============================================================================
-- MPCabinet Ecosystem - Shared Schema for Analytics
-- ============================================================================
-- Эта миграция создаёт общую схему для всех ботов экосистемы
-- Размещается в postgres/init/02-analytics.sql для автоматического выполнения

-- Создание схемы
CREATE SCHEMA IF NOT EXISTS shared;

-- ============================================================================
-- Таблица: shared.users
-- ============================================================================
-- Глобальный реестр пользователей из всех ботов экосистемы

CREATE TABLE IF NOT EXISTS shared.users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    language_code TEXT,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_users_username ON shared.users(username);
CREATE INDEX IF NOT EXISTS idx_users_first_seen ON shared.users(first_seen DESC);

-- Комментарии
COMMENT ON TABLE shared.users IS 'Глобальный реестр пользователей из всех ботов экосистемы';
COMMENT ON COLUMN shared.users.telegram_id IS 'Уникальный ID пользователя Telegram';
COMMENT ON COLUMN shared.users.first_seen IS 'Первое обращение к любому боту экосистемы';
COMMENT ON COLUMN shared.users.last_seen IS 'Последнее обращение к любому боту';

-- ============================================================================
-- Таблица: shared.analytics_events
-- ============================================================================
-- Все события из всех ботов экосистемы

CREATE TABLE IF NOT EXISTS shared.analytics_events (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT REFERENCES shared.users(telegram_id) ON DELETE SET NULL,
    bot_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_analytics_telegram_id ON shared.analytics_events(telegram_id);
CREATE INDEX IF NOT EXISTS idx_analytics_bot_event ON shared.analytics_events(bot_name, event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON shared.analytics_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_event_data ON shared.analytics_events USING GIN (event_data);

-- Комментарии
COMMENT ON TABLE shared.analytics_events IS 'События из всех ботов экосистемы';
COMMENT ON COLUMN shared.analytics_events.bot_name IS 'Имя бота (например: Picture Bot, CRM Bot)';
COMMENT ON COLUMN shared.analytics_events.event_type IS 'Тип события (user_start, error, бот-специфичные)';
COMMENT ON COLUMN shared.analytics_events.event_data IS 'Дополнительные данные события в формате JSONB';
```

### Приложение C: Шаблон main.py для нового бота

См. файл: `ecosystem_shared/templates/main.py.template`

(Полный код уже представлен в разделе 3.2)

### Приложение D: Шаблон .env

См. файл: `ecosystem_shared/templates/.env.template`

(Полный код уже представлен в разделе 8)

### Приложение E: Checklist для создания нового бота

**Перед началом разработки:**

- [ ] Создан новый Git-репозиторий
- [ ] Скопирована папка `ecosystem_shared/` из Picture Bot репозитория
- [ ] Создан `.gitignore` (включает `.env`)

**Конфигурация:**

- [ ] Создан `config/settings.py` с наследованием от `BaseSettings`
- [ ] Создан `.env` файл на основе шаблона
- [ ] Заполнены обязательные переменные: `BOT_TOKEN`, `DATABASE_URL`, `ANALYTICS_CHANNEL_ID`
- [ ] Создан `requirements.txt` (базовые + специфичные зависимости)

**Код бота:**

- [ ] Создан `main.py` на основе шаблона
- [ ] Импортированы shared компоненты (db, services, middlewares)
- [ ] Зарегистрированы middleware (rate_limiter, error_handler)
- [ ] Инициализирован пул PostgreSQL
- [ ] Настроен APScheduler для дайджеста
- [ ] Реализован /start handler с `track_user_start()`
- [ ] Добавлены ваши handlers

**Аналитика:**

- [ ] Все handlers вызывают `track_event()` для важных действий
- [ ] Медиа трекается через callback pattern (после отправки)
- [ ] Ошибки трекаются через `track_error()`

**Деплой:**

- [ ] Создан `Dockerfile`
- [ ] Добавлен сервис в `docker-compose.yml` на VPS
- [ ] SQL миграция скопирована в `postgres/init/` (если есть бот-специфичные таблицы)
- [ ] Бот добавлен в analytics канал как администратор
- [ ] Протестирован запуск: `docker compose up -d --build bot-your-new-bot`
- [ ] Проверены логи: `docker compose logs -f bot-your-new-bot`

**Мониторинг:**

- [ ] Проверена запись событий в БД
- [ ] Получено уведомление о новом пользователе в канале
- [ ] Дайджест придёт в 00:00 МСК (подождите до следующего дня)

---

## Контакты и поддержка

**GitHub Issues:** Для багов и feature requests
**Telegram сообщество:** https://t.me/+R0Px1RRDjnQwZjQy (MPCabinet экосистема)

**Документация:**
- [Picture Bot README](README.md) - основная документация Picture Bot
- [Picture Bot CONTEXT](CONTEXT.md) - техническая документация
- [VDS.md](docs/VDS.md) - инструкции по деплою на Timeweb Cloud

---

**Последнее обновление:** 22.01.2026
**Автор:** Claude Sonnet 4.5
**Версия документа:** 1.0
