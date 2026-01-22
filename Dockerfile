FROM python:3.11-slim

WORKDIR /app

# Установка ffmpeg для конвертации HLS видео
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Запуск бота
CMD ["python", "main.py"]
