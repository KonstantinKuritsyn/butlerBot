# Развертывание Butler Bot на Linux сервере

Подробная инструкция по развертыванию Butler Bot на Linux сервере через обычный Docker (без docker-compose).

## Предварительные требования

- Linux сервер с правами sudo
- Docker установлен и запущен
- Доступ к интернету
- Telegram Bot Token
- WeatherAPI Token

## Шаг 1: Установка Docker (если не установлен)

### Ubuntu/Debian:
```bash
# Обновление пакетов
sudo apt update

# Установка необходимых пакетов
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление официального GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перезагрузка для применения изменений группы
sudo systemctl enable docker
sudo systemctl start docker
```

### CentOS/RHEL:
```bash
# Установка утилит
sudo yum install -y yum-utils

# Добавление репозитория Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Установка Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Запуск и автозапуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

После установки перелогиньтесь или выполните:
```bash
newgrp docker
```

## Шаг 2: Подготовка файлов на сервере

### Создание директории проекта:
```bash
mkdir -p ~/butler-bot
cd ~/butler-bot
```

### Создание Dockerfile:
```bash
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директории для данных
RUN mkdir -p /app/data

# Создание пользователя для безопасности
RUN useradd -m -s /bin/bash botuser && \
    chown -R botuser:botuser /app

USER botuser

CMD ["python", "main.py"]
EOF
```

### Создание requirements.txt:
```bash
cat > requirements.txt << 'EOF'
python-telegram-bot[job-queue]==20.7
pytz==2023.3
python-dotenv==1.0.0
requests==2.31.0
EOF
```

### Создание файла .env:
```bash
cat > .env << 'EOF'
# Замените на ваши реальные токены
TELEGRAM_TOKEN_WISH_BOT=ваш_токен_от_BotFather
WEATHER_API_TOKEN=ваш_токен_от_WeatherAPI
EOF
```

**⚠️ ВАЖНО:** Отредактируйте файл `.env` и замените токены на реальные:
```bash
nano .env
```

## Шаг 3: Загрузка исходного кода

Есть несколько способов получить исходный код:

### Вариант A: Клонирование из Git (если есть репозиторий):
```bash
git clone your-repository-url .
```

### Вариант B: Загрузка файлов по отдельности

Создайте каждый файл вручную или загрузите через scp/sftp:

#### main.py:
```bash
# Создайте файл main.py и скопируйте содержимое
nano main.py
```

#### database.py:
```bash
# Создайте файл database.py и скопируйте содержимое
nano database.py
```

#### weather.py:
```bash
# Создайте файл weather.py и скопируйте содержимое
nano weather.py
```

#### reminders.py:
```bash
# Создайте файл reminders.py и скопируйте содержимое
nano reminders.py
```

#### keyboard_utils.py:
```bash
# Создайте файл keyboard_utils.py и скопируйте содержимое
nano keyboard_utils.py
```

### Вариант C: Загрузка через scp с локальной машины:
```bash
# На локальной машине (откуда копируете)
scp -r /path/to/butlerBot/* user@your-server-ip:~/butler-bot/
```

## Шаг 4: Сборка Docker образа

```bash
cd ~/butler-bot

# Сборка образа
docker build -t butler-bot:latest .
```

Процесс может занять несколько минут. При успешной сборке увидите:
```
Successfully tagged butler-bot:latest
```

## Шаг 5: Создание Docker volume для данных

```bash
# Создание volume для постоянного хранения данных
docker volume create butler-data
```

## Шаг 6: Запуск контейнера

### Основная команда запуска:
```bash
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
```

### Объяснение параметров:
- `-d` - запуск в фоновом режиме
- `--name butler-bot` - имя контейнера
- `--restart unless-stopped` - автоматический перезапуск
- `-v butler-data:/app/data` - монтирование volume для данных
- `--env-file .env` - загрузка переменных окружения
- `butler-bot:latest` - имя образа

## Шаг 7: Проверка работы

### Просмотр логов:
```bash
docker logs butler-bot
```

Успешный запуск покажет:
```
✅ Миграция: добавлена колонка weather_time
🤖 Butler Bot запущен...
🌤️ Погода: персональные настройки времени
📅 Проверка задач: каждую минуту
⏰ Проверка напоминаний: каждую минуту
⚙️ Персональные настройки: доступны
```

### Просмотр статуса контейнера:
```bash
docker ps
```

### Просмотр логов в реальном времени:
```bash
docker logs -f butler-bot
```

## Управление контейнером

### Остановка:
```bash
docker stop butler-bot
```

### Запуск:
```bash
docker start butler-bot
```

### Перезапуск:
```bash
docker restart butler-bot
```

### Удаление контейнера:
```bash
docker stop butler-bot
docker rm butler-bot
```

### Обновление кода:
```bash
# Остановка и удаление старого контейнера
docker stop butler-bot
docker rm butler-bot

# Пересборка образа с новым кодом
docker build -t butler-bot:latest .

# Запуск нового контейнера
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
```

## Работа с данными

### Резервное копирование базы данных:
```bash
# Создание резервной копии
docker run --rm \
  -v butler-data:/data \
  -v $(pwd):/backup \
  ubuntu:20.04 \
  cp /data/butler_bot.db /backup/butler_bot_backup_$(date +%Y%m%d_%H%M%S).db
```

### Восстановление базы данных:
```bash
# Восстановление из резервной копии
docker run --rm \
  -v butler-data:/data \
  -v $(pwd):/backup \
  ubuntu:20.04 \
  cp /backup/butler_bot_backup_YYYYMMDD_HHMMSS.db /data/butler_bot.db
```

### Просмотр содержимого базы данных:
```bash
# Вход в контейнер для работы с БД
docker exec -it butler-bot sqlite3 /app/data/butler_bot.db

# Просмотр таблиц
.tables

# Выход
.quit
```

## Мониторинг и логирование

### Настройка ротации логов:
```bash
# Создание конфигурации для logrotate
sudo cat > /etc/logrotate.d/docker-butler-bot << 'EOF'
/var/lib/docker/containers/*/butler-bot*-json.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
    postrotate
        docker kill --signal="USR1" butler-bot 2>/dev/null || true
    endscript
}
EOF
```

### Мониторинг ресурсов:
```bash
# Просмотр использования ресурсов
docker stats butler-bot

# Просмотр информации о контейнере
docker inspect butler-bot
```

## Автозапуск при перезагрузке сервера

Docker контейнер автоматически запустится при перезагрузке благодаря флагу `--restart unless-stopped`.

Для дополнительной надежности можно создать systemd сервис:

```bash
sudo cat > /etc/systemd/system/butler-bot.service << 'EOF'
[Unit]
Description=Butler Bot Container
Requires=docker.service
After=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a butler-bot
ExecStop=/usr/bin/docker stop butler-bot

[Install]
WantedBy=multi-user.target
EOF

# Включение сервиса
sudo systemctl enable butler-bot.service
```

## Безопасность

### Настройка файрвола (UFW):
```bash
# Если используете UFW
sudo ufw allow ssh
sudo ufw enable
```

### Обновление системы:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### Регулярные обновления Docker образа:
```bash
# Создание скрипта обновления
cat > ~/update-butler-bot.sh << 'EOF'
#!/bin/bash
cd ~/butler-bot
docker pull python:3.12-slim
docker build -t butler-bot:latest .
docker stop butler-bot
docker rm butler-bot
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
EOF

chmod +x ~/update-butler-bot.sh
```

## Устранение неполадок

### Проблемы с правами доступа:
```bash
# Если проблемы с правами на файлы
sudo chown -R $USER:$USER ~/butler-bot
```

### Проблемы с сетью:
```bash
# Проверка сетевого подключения
docker run --rm alpine:latest ping -c 4 google.com
```

### Очистка Docker системы:
```bash
# Очистка неиспользуемых ресурсов
docker system prune -a

# Просмотр использования дискового пространства
docker system df
```

### Проблемы с токенами:
```bash
# Проверка переменных окружения в контейнере
docker exec butler-bot env | grep TOKEN
```

## Заключение

После выполнения всех шагов Butler Bot будет работать на вашем Linux сервере в Docker контейнере с:

- ✅ Автоматическим перезапуском при сбоях
- ✅ Постоянным хранением данных
- ✅ Изолированной средой выполнения
- ✅ Простым управлением через Docker команды

Для получения помощи или при возникновении проблем проверьте логи контейнера: `docker logs butler-bot`
