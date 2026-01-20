# CONTEXT.md — Техническая документация проекта

**Версия:** 0.3.2
**Обновлено:** 20.01.2026

---

## Оглавление

1. [Общая архитектура](#общая-архитектура)
2. [Эволюция проекта (версии 0.1.x → 0.3.2)](#эволюция-проекта)
3. [Структура кода](#структура-кода)
4. [Ключевые компоненты](#ключевые-компоненты)
5. [Алгоритмы поиска медиа](#алгоритмы-поиска-медиа)
6. [Кеширование и оптимизации](#кеширование-и-оптимизации)
7. [Обработка ошибок](#обработка-ошибок)
8. [Тестирование](#тестирование)
9. [Метрики производительности](#метрики-производительности)

---

## Общая архитектура

### Принципы построения

**Wildberries Media Bot** построен по принципу **асинхронного event-driven приложения** на базе фреймворка [aiogram 3](https://docs.aiogram.dev/en/latest/).

**Ключевые паттерны:**
- **Async/await everywhere** — все I/O операции асинхронные
- **Dependency Injection** — Settings через Pydantic, Bot через конструкторы
- **Middleware pattern** — глобальная обработка ошибок
- **Decorator pattern** — логирование, retry, timing
- **Context Manager pattern** — автоматическое управление HTTP сессиями
- **Observer pattern** — progress_callback для обновления UI

### Технологический стек

| Компонент | Технология | Версия | Назначение |
|-----------|-----------|--------|------------|
| Runtime | Python | 3.10+ | Основной язык |
| Bot Framework | aiogram | 3.x | Telegram Bot API |
| HTTP Client | aiohttp | 3.x | Асинхронные HTTP запросы |
| Validation | pydantic | 2.x | Settings и конфигурация |
| Testing | pytest + pytest-asyncio | 7.x + 0.21.x | Unit-тестирование |
| Media Processing | ffmpeg | - | HLS → MP4 конвертация |

---

## Эволюция проекта

### Версия 0.1.x — Базовый функционал

**Основные возможности:**
- Парсинг артикулов и ссылок WB
- Поиск фото и видео через CDN
- Отправка медиа в Telegram
- Базовое логирование

**Проблемы:**
- Долгий поиск basket (до 90 сек)
- Синхронный поиск видео блокировал UI
- Нет кеширования (повторные запросы медленные)
- Время показа карточки: ~40 секунд

### Версия 0.2.x — HLS конвертация и оптимизации

**0.2.0** — HLS → MP4 конвертация
- Добавлен `HLSConverter` для поддержки современных видео WB
- Интеграция с ffmpeg
- Исключения: `HLSConversionError`, `FFmpegNotFoundError`

**0.2.6** — Оптимизация поиска basket
- Параллельная проверка всех 100 basket
- Ускорение с 2-4 сек до 1-2 сек

**0.2.7** — Ленивая загрузка медиа
- Параметры `skip_video` и `skip_photos`
- Немедленный показ карточки без ожидания видео
- Ускорение показа карточки с 40 сек до 6 сек

### Версия 0.3.x — Прогресс в реальном времени и кеширование

**0.3.0** — Прогресс поиска видео в реальном времени
- Фоновый поиск через `asyncio.create_task()`
- Callback-система для обновления UI
- Live-прогресс: "🎥 Видео: ⏳ ищем 0%" → "10%" → "есть ✅"
- Немедленный отклик пользователю (показ карточки за 2-6 сек)

**0.3.1** — Обновлённый формат карточки товара
- Компактная первая строка: `✅Товар: {nm_id} — найден!`
- Улучшенное визуальное разделение
- Убран emoji 📦

**0.3.2** — Кеширование найденных видео URLs (текущая версия)
- Добавлен `VideoCache` с TTL 1 час
- Ускорение повторных запросов с 10-30 сек до 1-2 сек
- Сохранение даже отрицательных результатов (None)

---

## Структура кода

### Дерево файлов

```
MPCabinet_Picture_Bot/
├── main.py                          # Точка входа
├── VERSION                          # Текущая версия (0.3.2)
├── .env                             # Конфигурация (не в git)
│
├── config/
│   └── settings.py                  # Pydantic Settings
│
├── bot/
│   ├── handlers/
│   │   ├── start.py                # /start, /help команды
│   │   ├── article.py              # Поиск товара по артикулу
│   │   └── callbacks.py            # Inline кнопки (фото/видео)
│   │
│   ├── keyboards/
│   │   └── inline.py               # Inline клавиатуры
│   │
│   └── middlewares/
│       └── error_handler.py        # ErrorHandlerMiddleware
│
├── services/
│   ├── wb_parser.py                # Парсинг WB API (542 строки)
│   ├── media_downloader.py         # Загрузка медиа (273 строки)
│   ├── hls_converter.py            # HLS → MP4 (142 строки) [0.2.0+]
│   └── video_cache.py              # Кеш видео URLs (91 строка) [0.3.2+]
│
├── utils/
│   ├── validators.py               # ArticleValidator
│   ├── logger.py                   # Настройка логирования
│   ├── exceptions.py               # Кастомные исключения (6 типов)
│   └── decorators.py               # Декораторы (3 типа)
│
├── tests/                          # 91 тест, 1750 строк
│   ├── conftest.py                 # Pytest фикстуры
│   ├── test_validators.py          # 18 тестов
│   ├── test_wb_parser.py           # 10 тестов
│   ├── test_media_downloader.py    # 11 тестов
│   ├── test_hls_converter.py       # 13 тестов
│   ├── test_video_cache.py         # 6 тестов
│   ├── test_decorators.py          # 10 тестов
│   └── test_handlers/              # 23 теста
│
└── docs/
    ├── PLAN.md                     # План разработки
    └── wb-api/                     # Справочник WB API (18 файлов)
```

### Зависимости между модулями

```
main.py
  ├─> config.settings (Settings)
  ├─> bot.handlers.* (Router'ы)
  └─> bot.middlewares.error_handler

bot.handlers.article
  ├─> utils.validators (ArticleValidator)
  ├─> services.wb_parser (WBParser)
  ├─> services.video_cache (get_video_cache)
  ├─> bot.keyboards.inline (get_media_type_keyboard)
  └─> utils.decorators (@retry_on_telegram_error)

bot.handlers.callbacks
  ├─> services.wb_parser (WBParser)
  ├─> services.media_downloader (MediaDownloader)
  └─> utils.decorators (@retry_on_telegram_error)

services.wb_parser
  ├─> config.settings (Settings)
  ├─> services.video_cache (VideoCache)
  └─> utils.exceptions (ProductNotFoundError, WBAPIError)

services.media_downloader
  ├─> services.hls_converter (HLSConverter)
  └─> utils.exceptions (NoMediaError, HLSConversionError)

services.hls_converter
  ├─> config.settings (Settings)
  └─> utils.exceptions (FFmpegNotFoundError, HLSConversionError)
```

---

## Ключевые компоненты

### 1. WBParser — Парсинг медиа Wildberries

**Файл:** [services/wb_parser.py](services/wb_parser.py)
**Строк кода:** 542

#### Назначение
Поиск фотографий и видео товаров через публичный CDN Wildberries.

#### Публичные методы

```python
async def get_product_media(
    self,
    nm_id: str,
    skip_video: bool = False,
    skip_photos: bool = False,
    progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
) -> ProductMedia:
    """
    Главный метод для получения медиа.

    Args:
        nm_id: Артикул товара (6-10 цифр)
        skip_video: Пропустить поиск видео (ленивая загрузка)
        skip_photos: Пропустить поиск фото
        progress_callback: Callback для обновления прогресса поиска видео (0-100%)

    Returns:
        ProductMedia с полями: nm_id, name, photos, video

    Raises:
        InvalidArticleError: Неверный формат артикула
        ProductNotFoundError: Товар не найден (basket не определен)
        NoMediaError: У товара нет ни фото, ни видео
        WBAPIError: Проблемы с API/сетью
    """
```

#### Внутренние методы (алгоритмы)

1. **`_find_basket(nm_id, vol, part)`** — Поиск рабочего basket
   - Проверка in-memory кеша `vol → basket`
   - Параллельная проверка всех 100 basket через `asyncio.gather()`
   - Сохранение в кеш при нахождении
   - Время: ~1-2 сек (с кешем мгновенно)

2. **`_find_photos(nm_id, vol, part, basket)`** — Поиск фотографий
   - Последовательный перебор номеров 1-20
   - Early exit при первом ненайденном (фото идут подряд)
   - HEAD запросы для скорости
   - Время: ~1-3 сек

3. **`_check_video(nm_id, progress_callback)`** — Поиск видео
   - Интеграция с `VideoCache` (проверка и сохранение)
   - Fallback: Legacy MP4 → HLS формат
   - Callback для обновления UI (каждые 10% или 2+ сек)
   - Время: 5-30 сек (первый раз), 1-2 сек (из кеша)

4. **`_find_video_hls(nm_id, progress_callback)`** — Поиск HLS видео
   - Приоритет: vol 1-50 (горячая зона), затем 51-200
   - Батчи по 100 комбинаций (basket × vol)
   - Timeout 30 секунд
   - Early exit при первом найденном
   - Прогресс callback с дебаунсингом

#### Особенности кеширования

```python
# Class-level переменная (общая для всех экземпляров)
_basket_cache: dict[int, int] = {}  # vol → basket

# Интеграция с VideoCache
from services.video_cache import get_video_cache
cache = get_video_cache()
found_in_cache, cached_video = cache.get(nm_id)

if found_in_cache:
    video = cached_video  # Может быть None
else:
    video = await self._check_video(nm_id)
    cache.set(nm_id, video)  # Сохранить даже None
```

#### HTTP сессия и лимиты

```python
# Настройка при входе в context manager
timeout = aiohttp.ClientTimeout(
    total=10,      # Общий timeout
    connect=5,     # Timeout соединения
    sock_read=5    # Timeout чтения
)

connector = aiohttp.TCPConnector(
    limit=100,           # Макс 100 соединений одновременно
    limit_per_host=50    # Макс 50 на один хост
)

self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
```

---

### 2. VideoCache — Кеш видео URLs

**Файл:** [services/video_cache.py](services/video_cache.py)
**Строк кода:** 91
**Версия:** 0.3.2+

#### Назначение
Кеширование найденных видео URLs для предотвращения повторного долгого поиска.

#### Архитектура

```python
class VideoCache:
    """
    In-memory кеш с TTL (Time To Live).
    Глобальный singleton через функцию get_video_cache().
    """

    def __init__(self, ttl_seconds: int = 3600):  # 1 час по умолчанию
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds
```

#### Структура записи

```python
{
    'url': Optional[str],    # URL видео или None если нет видео
    'timestamp': float       # time.time() момента сохранения
}
```

#### Публичные методы

```python
def get(self, nm_id: str) -> Tuple[bool, Optional[str]]:
    """
    Получить из кеша.

    Returns:
        (found, url) где:
        - found=True если запись в кеше и не истекла
        - url может быть None если у товара нет видео
    """

def set(self, nm_id: str, url: Optional[str]) -> None:
    """
    Сохранить в кеш.

    ВАЖНО: Сохраняет даже None (отрицательный результат).
    Это предотвращает повторный поиск для товаров без видео.
    """

def clear_expired(self) -> int:
    """
    Удалить истекшие записи.

    Returns:
        Количество удалённых записей
    """
```

#### Использование

```python
from services.video_cache import get_video_cache

# Проверка кеша
cache = get_video_cache()
found_in_cache, cached_video = cache.get(nm_id)

if found_in_cache:
    logger.info(f"Video cache HIT for {nm_id}")
    return cached_video
else:
    logger.info(f"Video cache MISS for {nm_id}, searching...")
    video = await _expensive_search(nm_id)
    cache.set(nm_id, video)
    return video
```

#### Метрики

- **Ускорение:** с 10-30 сек до 1-2 сек (при HLS нужна только конвертация)
- **Размер кеша:** Неограничен (in-memory), очистка через TTL
- **TTL:** 1 час (можно настроить в конструкторе)

---

### 3. MediaDownloader — Отправка медиа в Telegram

**Файл:** [services/media_downloader.py](services/media_downloader.py)
**Строк кода:** 273

#### Назначение
Загрузка медиа с WB CDN и отправка в Telegram с обработкой HLS конвертации.

#### Публичные методы

```python
async def send_photos(
    self,
    chat_id: int,
    media: ProductMedia,
    status_msg: Message
) -> None:
    """
    Отправка фотографий группами по 10.

    - Использует URLInputFile (Telegram скачивает сам)
    - Live-обновление прогресса: "Загружаю фото 5/15..."
    - Батчи по 10 из-за лимита sendMediaGroup
    """

async def send_video(
    self,
    chat_id: int,
    media: ProductMedia,
    status_msg: Message
) -> None:
    """
    Отправка видео с HLS конвертацией при необходимости.

    Алгоритм:
    1. Проверка is_hls_url() → определение формата
    2. Если HLS: конвертация через HLSConverter
    3. Если MP4: прямая отправка через URLInputFile
    4. Cleanup временных файлов в finally
    """

async def send_both(
    self,
    chat_id: int,
    media: ProductMedia,
    status_msg: Message
) -> None:
    """
    Последовательная отправка: сначала фото, потом видео.

    Graceful degradation: если видео не отправилось, фото уже у пользователя.
    """
```

#### Обработка HLS видео

```python
is_hls = HLSConverter.is_hls_url(media.video)
temp_path = None

try:
    if is_hls:
        await status_msg.edit_text("🎥 Конвертирую видео (HLS → MP4)...")

        converter = HLSConverter()
        temp_path = await converter.convert_hls_to_mp4(media.video, nm_id=media.nm_id)
        video_input = FSInputFile(temp_path)  # Локальный файл

        await status_msg.edit_text("🎥 Отправляю видео...")
    else:
        # Прямой MP4 URL
        await status_msg.edit_text("🎥 Загружаю видео...")
        video_input = URLInputFile(media.video)

    await self.bot.send_video(
        chat_id=chat_id,
        video=video_input,
        caption=f"Видео: {media.name}",
        request_timeout=120
    )
finally:
    # Очистка временного файла
    if temp_path and converter:
        converter.cleanup_temp_file(temp_path)
```

#### Обработка ошибок

```python
except FFmpegNotFoundError:
    await status_msg.edit_text("❌ Сервер не поддерживает HLS видео (ffmpeg не установлен)")
except HLSConversionError as e:
    await status_msg.edit_text(f"❌ Ошибка конвертации видео: {e}")
except Exception as e:
    await status_msg.edit_text("❌ Не удалось загрузить видео (лимит 50 MB)")
```

---

### 4. HLSConverter — Конвертация HLS в MP4

**Файл:** [services/hls_converter.py](services/hls_converter.py)
**Строк кода:** 142
**Версия:** 0.2.0+

#### Проблема
Telegram не воспроизводит HLS плейлисты (.m3u8) напрямую. Современные видео WB используют HLS формат.

#### Решение
Конвертация HLS → MP4 через ffmpeg перед отправкой.

#### Публичные методы

```python
@staticmethod
def is_hls_url(url: str) -> bool:
    """Определение HLS URL по расширению .m3u8 или /hls/ в пути."""

async def check_ffmpeg_available() -> bool:
    """Проверка доступности ffmpeg в системе."""

async def convert_hls_to_mp4(hls_url: str, nm_id: str = "video") -> Path:
    """
    Конвертация HLS → MP4.

    Args:
        hls_url: URL HLS плейлиста (.m3u8)
        nm_id: Артикул для имени файла

    Returns:
        Path к временному MP4 файлу

    Raises:
        FFmpegNotFoundError: ffmpeg не установлен
        HLSConversionError: Ошибка конвертации или timeout
    """

def cleanup_temp_file(path: Optional[Path]) -> None:
    """Удаление временного файла."""
```

#### Команда ffmpeg

```bash
ffmpeg -i "{hls_url}" -c copy -bsf:a aac_adtstoasc -y "{output.mp4}"
```

**Параметры:**
- `-i` — входной HLS URL
- `-c copy` — без перекодирования (быстрая копия потоков)
- `-bsf:a aac_adtstoasc` — фикс AAC аудио для MP4 контейнера
- `-y` — перезапись если файл существует

#### Timeout и лимиты

```python
# Из config/settings.py
HLS_CONVERT_TIMEOUT = 300  # 5 минут максимум
HLS_MAX_VIDEO_SIZE_MB = 50  # Лимит Telegram для URLInputFile

# Выполнение с timeout
process = await asyncio.create_subprocess_exec(*cmd, ...)

try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=self.settings.HLS_CONVERT_TIMEOUT
    )
except asyncio.TimeoutError:
    process.kill()
    self.cleanup_temp_file(output_path)
    raise HLSConversionError("Timeout конвертации (5 минут)")
```

#### Временные файлы

```python
# Директория для временных файлов
temp_dir = Path(self.settings.HLS_TEMP_DIR or tempfile.gettempdir())

# Имя файла с timestamp для уникальности
timestamp = int(time.time())
output_path = temp_dir / f"wb_video_{nm_id}_{timestamp}.mp4"

# Очистка в finally блоке
try:
    # конвертация и отправка
finally:
    converter.cleanup_temp_file(output_path)
```

---

### 5. Декораторы (utils/decorators.py)

**Файл:** [utils/decorators.py](utils/decorators.py)

#### @log_execution_time()

Логирование времени выполнения функций.

```python
@log_execution_time()
async def get_product_media(self, nm_id: str):
    # код функции
    pass

# Лог:
# 🔍 get_product_media() - START
# ✅ get_product_media() завершена за 2.345s
```

**Особенности:**
- Автоопределение async/sync через `inspect.iscoroutinefunction`
- Измерение через `time.perf_counter()`
- Логирование ERROR при исключениях

#### @log_function_call(log_args=False)

Детальное логирование вызовов с аргументами (опционально).

```python
@log_function_call(log_args=True)
def process_article(article: str):
    pass

# Лог:
# 📞 CALL process_article(article='12345678')
```

**Внимание:** `log_args=True` может логировать чувствительные данные!

#### @retry_on_telegram_error(max_retries=3, delay=1.0)

Автоматические повторы при сетевых ошибках Telegram.

```python
@retry_on_telegram_error(max_retries=3, delay=1.0)
async def send_message(message: Message):
    await message.answer("Hello")

# При TelegramNetworkError:
# Попытка 1/3 - ошибка, ждем 1 сек
# Попытка 2/3 - ошибка, ждем 2 сек  (экспоненциальная задержка)
# Попытка 3/3 - успех
```

**Обрабатываемые ошибки:**
- `TelegramNetworkError`
- `ClientConnectorError`
- `ClientOSError`
- `TimeoutError`
- `ServerDisconnectedError`

**Стратегия:**
- Экспоненциальная задержка: `delay * (2 ** (attempt - 1))`
- Другие исключения пробрасываются без retry

---

## Алгоритмы поиска медиа

### Формулы URL медиа Wildberries

**Фото:**
```
https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nmId}/images/big/{N}.webp
```

**Видео Legacy MP4:**
```
https://video.wildberries.ru/{nmId}/{nmId}.mp4
```

**Видео HLS (современный):**
```
https://videonme-basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nmId}/hls/1440p/index.m3u8
```

**Вычисления:**
```python
vol = nm_id_int // 100000       # Для фото
part = nm_id_int // 1000        # Для фото

vol_video = nm_id_int // 100000  # Для видео
part_video = nm_id_int // 10000  # Для видео (делим на 10000, не 1000!)
basket = ???                     # Определяется перебором
```

### Алгоритм поиска basket

**Проблема:** Basket не вычисляется по формуле, только перебором.

**Решение:**

```python
async def _find_basket(self, nm_id: str, vol: int, part: int) -> Optional[int]:
    # 1. Проверка in-memory кеша
    if vol in self._basket_cache:
        cached_basket = self._basket_cache[vol]
        if await self._check_single_basket(nm_id, vol, part, cached_basket):
            return cached_basket

    # 2. Параллельная проверка всех 100 basket
    all_baskets = list(range(1, 101))  # 1-100
    tasks = [self._check_single_basket(nm_id, vol, part, b) for b in all_baskets]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Early exit при первом найденном
    for basket, result in zip(all_baskets, results):
        if result is True:
            self._basket_cache[vol] = basket  # Сохранение в кеш
            return basket

    return None  # Basket не найден (товар удалён)
```

**Время:** ~1-2 сек (все 100 запросов параллельно)

### Алгоритм поиска HLS видео

**Проблема:** 20000 возможных комбинаций (basket 1-100 × vol 1-200).

**Решение:** Приоритизация и батчевая обработка.

```python
async def _find_video_hls(self, nm_id: str, progress_callback) -> Optional[str]:
    # 1. Приоритет: горячая зона vol 1-50 (99% видео здесь)
    hot_combinations = [
        (basket, vol)
        for basket in range(1, 101)
        for vol in range(1, 51)
    ]  # 5000 комбинаций

    # 2. Расширенная зона vol 51-200
    extended_combinations = [
        (basket, vol)
        for basket in range(1, 101)
        for vol in range(51, 201)
    ]  # 15000 комбинаций

    all_combinations = hot_combinations + extended_combinations

    # 3. Батчевая проверка по 100 комбинаций
    BATCH_SIZE = 100
    for i in range(0, len(all_combinations), BATCH_SIZE):
        # Timeout check (30 сек максимум)
        if time.time() - start_time > 30:
            return None

        batch = all_combinations[i:i + BATCH_SIZE]

        # Progress callback (каждые 10% или 2+ сек)
        progress = int((i // BATCH_SIZE / total_batches) * 100)
        if should_update_progress(progress):
            await progress_callback(progress)

        # Параллельная проверка батча
        result = await self._check_video_batch(nm_id, part, batch)

        if result:
            basket, vol = result
            return f"https://videonme-basket-{basket:02d}.wbbasket.ru/..."

        await asyncio.sleep(0.01)  # 10ms между батчами

    return None
```

**Время:** 5-30 сек (зависит от расположения видео в пространстве basket × vol)

---

## Кеширование и оптимизации

### 1. In-memory кеш basket (vol → basket)

```python
# Class-level (общий для всех экземпляров WBParser)
_basket_cache: dict[int, int] = {}

# Зачем: Товары с одинаковым vol часто используют один basket
# TTL: Нет (живёт весь uptime процесса)
# Размер: Неограничен (но vol уникальных не так много)
```

### 2. VideoCache (nm_id → video URL)

```python
# Singleton через get_video_cache()
_cache: Dict[str, Dict] = {}

# Зачем: Избежать повторного 10-30 сек поиска видео
# TTL: 1 час (видео могут добавляться/удаляться)
# Размер: Неограничен, автоматическая очистка истекших
# Особенность: Сохраняет даже None (товары без видео)
```

### 3. Параллелизм (asyncio.gather)

**Поиск basket:**
```python
tasks = [check_basket(b) for b in range(1, 101)]
results = await asyncio.gather(*tasks, return_exceptions=True)
# 100 запросов одновременно за ~1-2 сек
```

**Поиск видео:**
```python
# Батчи по 100 комбинаций
batch = [(basket, vol) for basket in range(1,101) for vol in range(1,51)][:100]
tasks = [check_video(b, v) for b, v in batch]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. Фоновые задачи (asyncio.create_task)

```python
# В article.py handler
async def search_video():
    video = await parser._check_video(nm_id, progress_callback)
    cache.set(nm_id, video)
    await update_ui(video)

# Запуск в фоне (не блокирует показ карточки)
asyncio.create_task(search_video())

# Пользователь видит карточку сразу, видео обновляется по мере поиска
```

### 5. Ленивая загрузка (skip_video/skip_photos)

```python
# Показ карточки: только фото, видео в фоне
media = await parser.get_product_media(nm_id, skip_video=True)

# Кнопка "Фото": только фото
media = await parser.get_product_media(nm_id, skip_video=True)

# Кнопка "Видео": только видео
media = await parser.get_product_media(nm_id, skip_photos=True)

# Кнопка "Всё": и фото, и видео
media = await parser.get_product_media(nm_id)
```

---

## Обработка ошибок

### Иерархия исключений

```python
WBBotException                          # Базовое (utils/exceptions.py)
├── InvalidArticleError                 # Неверный формат артикула
├── ProductNotFoundError                # Товар не найден (basket не определен)
├── NoMediaError                        # Нет ни фото, ни видео
├── WBAPIError                          # Ошибка API/сети
└── HLSConversionError                  # Ошибка конвертации HLS (0.2.0+)
    └── FFmpegNotFoundError             # ffmpeg не установлен
```

### Уровни обработки

**1. Handler level (специфичная обработка)**

```python
# bot/handlers/article.py
try:
    media = await parser.get_product_media(nm_id)
except InvalidArticleError:
    await message.answer("❌ Неверный формат артикула")
except ProductNotFoundError:
    await message.answer("❌ Товар не найден")
except NoMediaError:
    await message.answer("❌ У товара нет фото/видео")
except WBAPIError:
    await message.answer("❌ Ошибка API Wildberries")
```

**2. Middleware level (глобальная сеть безопасности)**

```python
# bot/middlewares/error_handler.py
class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            # Попытка отправить пользователю
            await event.answer("❌ Произошла ошибка. Попробуйте позже.")
```

**3. Decorator level (retry для сетевых ошибок)**

```python
@retry_on_telegram_error(max_retries=3)
async def send_message(message):
    # Автоматические повторы при TelegramNetworkError
    await message.answer("Hello")
```

---

## Тестирование

### Статистика

- **Всего тестов:** 91
- **Покрытие:** 82%
- **Тестовый код:** ~1750 строк
- **Фреймворк:** pytest + pytest-asyncio

### Структура тестов

| Модуль | Тестов | Покрывает |
|--------|--------|-----------|
| test_validators.py | 18 | ArticleValidator (артикулы и ссылки) |
| test_wb_parser.py | 10 | WBParser (поиск медиа, кеш basket) |
| test_media_downloader.py | 11 | MediaDownloader (отправка фото/видео) |
| test_hls_converter.py | 13 | HLSConverter (конвертация, ffmpeg) |
| test_video_cache.py | 6 | VideoCache (кеш, TTL, очистка) |
| test_decorators.py | 10 | Декораторы (timing, retry, logging) |
| test_article_handler.py | 8 | Обработчик артикулов |
| test_callbacks_handler.py | 7 | Обработчик кнопок |
| test_start_handler.py | 2 | Команды /start, /help |

### Ключевые фикстуры (conftest.py)

```python
@pytest.fixture
def message():
    """Mock aiogram Message."""
    mock_msg = AsyncMock(spec=Message)
    mock_msg.answer = AsyncMock()
    return mock_msg

@pytest.fixture
def aioresponse():
    """Mock aiohttp запросов."""
    with aioresponses() as m:
        yield m

@pytest.fixture
def product_media():
    """Тестовые данные ProductMedia."""
    return ProductMedia(
        nm_id="12345678",
        name="Test Product",
        photos=["https://basket-01.wbbasket.ru/.../1.webp"],
        video="https://video.wildberries.ru/.../12345678.mp4"
    )
```

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=. --cov-report=term-missing

# Конкретный файл
pytest tests/test_video_cache.py -v

# С логами
pytest tests/ -v -s
```

---

## Метрики производительности

### Среднее время операций (версия 0.3.2)

| Операция | Время | Кеш | Примечание |
|----------|-------|-----|------------|
| Показ карточки товара | 2-6 сек | - | Только фото, видео в фоне |
| Поиск basket | 1-2 сек | ~0 сек | In-memory кеш vol → basket |
| Поиск фото (1-10 шт) | 1-3 сек | - | Последовательный перебор |
| Поиск видео (первый раз) | 5-30 сек | - | Перебор 5000-20000 комбинаций |
| Поиск видео (из кеша) | 1-2 сек | ✅ | Только HLS конвертация если нужна |
| HLS → MP4 конвертация | 1-3 сек | - | Зависит от размера видео |
| Отправка 10 фото | 3-5 сек | - | Через URLInputFile |
| Отправка видео MP4 | 2-5 сек | - | Через URLInputFile |
| Отправка видео HLS | 3-8 сек | - | С конвертацией |

### Сравнение версий (время показа карточки товара)

| Версия | Время | Улучшение | Причина |
|--------|-------|-----------|---------|
| 0.1.x | ~40 сек | - | Синхронный поиск фото + видео |
| 0.2.7 | ~6 сек | 7x | Ленивая загрузка (skip_video) |
| 0.3.0 | ~2-6 сек | 10x | Фоновый поиск видео |

### Сравнение версий (повторный запрос видео)

| Версия | Время | Улучшение | Причина |
|--------|-------|-----------|---------|
| 0.1.x - 0.3.1 | 10-30 сек | - | Повторный поиск |
| 0.3.2 | 1-2 сек | 15x | VideoCache |

### Статистика HTTP запросов

**Поиск одного товара (среднее):**
- Basket поиск: 50-100 HEAD запросов (параллельно)
- Фото поиск: 5-10 HEAD запросов (последовательно)
- Видео поиск: 500-5000 HEAD запросов (батчами по 100)

**Итого:** 555-5110 запросов на товар (первый раз)

**С кешированием:**
- Basket поиск: 0 запросов (кеш)
- Фото поиск: 5-10 HEAD запросов
- Видео поиск: 0 запросов (кеш)

**Итого:** 5-10 запросов на товар (повторный)

### Лимиты Telegram Bot API

| Ресурс | Лимит | Обход |
|--------|-------|-------|
| Фото через URL | 5 MB | URLInputFile |
| Видео через URL | 20 MB | Лимит Telegram, обойти нельзя |
| sendMediaGroup | 2-10 файлов | Батчи по 10 |
| Одновременные запросы | ~30-50 | Встроенные лимиты aiogram |

---

## Итоги

**Wildberries Media Bot 0.3.2** — зрелое асинхронное приложение с:
- ✅ Фоновым поиском видео (не блокирует UI)
- ✅ Многоуровневым кешированием (basket + video URLs)
- ✅ HLS конвертацией через ffmpeg
- ✅ Прогрессом в реальном времени
- ✅ 82% покрытием тестами
- ✅ Детальным логированием
- ✅ Graceful degradation при ошибках

**Производительность:** показ карточки товара за 2-6 сек (было 40 сек в v0.1.x).

**Надёжность:** 91 тест, автоматические retry, глобальная обработка ошибок.
