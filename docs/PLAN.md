# План: HLS → MP4 конвертация для Telegram

**Обновлено:** 19.01.2026 (версия 0.2.0)

## Проблема

Telegram не воспроизводит HLS плейлисты (m3u8). Текущий код отправляет URL напрямую через `URLInputFile`, что работает только для MP4.

**Пример HLS URL:**
```
https://videonme-basket-01.wbbasket.ru/vol3/part40444/404448483/hls/1440p/index.m3u8
```

## Решение

Конвертация HLS → MP4 через ffmpeg перед отправкой в Telegram.

---

## Критические файлы

| Файл | Действие |
|------|----------|
| `services/hls_converter.py` | **СОЗДАТЬ** - класс HLSConverter |
| `services/media_downloader.py` | Изменить send_video() |
| `utils/exceptions.py` | Добавить HLSConversionError |
| `config/settings.py` | Добавить FFMPEG_* настройки |
| `tests/test_hls_converter.py` | **СОЗДАТЬ** - тесты |

---

## Этапы реализации

### 1. Исключения (`utils/exceptions.py`)

```python
class HLSConversionError(WBBotException):
    """Ошибка конвертации HLS видео."""
    pass

class FFmpegNotFoundError(HLSConversionError):
    """ffmpeg не установлен."""
    pass
```

### 2. Настройки (`config/settings.py`)

```python
FFMPEG_PATH: str = "ffmpeg"
HLS_CONVERT_TIMEOUT: int = 300  # 5 минут
HLS_TEMP_DIR: str | None = None  # системная temp
HLS_MAX_VIDEO_SIZE_MB: int = 50
```

### 3. Конвертер (`services/hls_converter.py`)

**Класс HLSConverter:**
- `is_hls_url(url)` - определение HLS по `.m3u8` или `/hls/`
- `check_ffmpeg_available()` - проверка ffmpeg в системе
- `convert_hls_to_mp4(hls_url, nm_id)` - конвертация через subprocess
- `cleanup_temp_file(path)` - удаление временного файла

**Команда ffmpeg:**
```bash
ffmpeg -i "HLS_URL" -c copy -bsf:a aac_adtstoasc output.mp4
```
- `-c copy` - без перекодирования (быстро)
- `-bsf:a aac_adtstoasc` - фикс AAC для MP4 контейнера

### 4. MediaDownloader (`services/media_downloader.py`)

**Изменения в send_video():**

```python
from aiogram.types import FSInputFile
from services.hls_converter import HLSConverter

async def send_video(self, chat_id, media, status_msg):
    is_hls = HLSConverter.is_hls_url(media.video)
    temp_path = None

    try:
        if is_hls:
            await status_msg.edit_text("🎥 Конвертирую видео...")
            converter = HLSConverter()
            temp_path = await converter.convert_hls_to_mp4(media.video, media.nm_id)
            video_input = FSInputFile(temp_path)
        else:
            video_input = URLInputFile(media.video)

        await self.bot.send_video(chat_id, video=video_input, ...)
    finally:
        if temp_path:
            HLSConverter().cleanup_temp_file(temp_path)
```

### 5. Тесты (`tests/test_hls_converter.py`)

- `test_is_hls_url_true/false` - определение HLS URL
- `test_check_ffmpeg_available` - проверка ffmpeg
- `test_convert_hls_timeout` - таймаут конвертации
- `test_cleanup_temp_file` - очистка временных файлов

---

## Системные требования

**ffmpeg должен быть установлен:**

```bash
# Windows
winget install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

## Верификация

1. **Unit тесты:**
   ```bash
   pytest tests/ -v
   ```

2. **Ручное тестирование:**
   - Отправить боту артикул с HLS видео (например, 404448483)
   - Проверить что видео конвертируется и отправляется
   - Проверить что временный файл удаляется

3. **Graceful degradation:**
   - Убрать ffmpeg из PATH
   - Проверить что бот выдаёт понятную ошибку

---

## Риски

| Риск | Митигация |
|------|-----------|
| ffmpeg не установлен | Сообщение пользователю + fallback |
| Большие видео (>50MB) | Warning в логах |
| Медленная конвертация | Timeout 5 минут + прогресс в UI |
| Temp файлы не удаляются | Cleanup в finally блоке |

---

## Версионирование

**Было:** 0.1.9
**Станет:** 0.2.0 (новый функционал)
