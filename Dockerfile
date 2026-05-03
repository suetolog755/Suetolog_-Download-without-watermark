FROM python:3.11-slim

WORKDIR /app

# Установка ffmpeg и системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего остального кода
COPY . .

# Создание папки для загрузок
RUN mkdir -p downloads

# Запуск бота
CMD ["python", "bot.py"]
