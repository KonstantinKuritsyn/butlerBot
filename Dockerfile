# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Настраиваем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Создаем пользователя для безопасности
RUN useradd -m -s /bin/bash botuser && \
    chown -R botuser:botuser /app
USER botuser

# Открываем порт (если понадобится в будущем)
EXPOSE 8080

# Команда запуска
CMD ["python", "main.py"]
