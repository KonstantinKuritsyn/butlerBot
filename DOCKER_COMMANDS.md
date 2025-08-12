# Команды Docker для Butler Bot

Справочник основных команд для управления Butler Bot через обычный Docker.

## Основные команды

### Сборка и запуск

```bash
# Сборка образа
docker build -t butler-bot:latest .

# Создание volume для данных
docker volume create butler-data

# Запуск контейнера
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
```

### Управление контейнером

```bash
# Просмотр статуса
docker ps

# Просмотр всех контейнеров (включая остановленные)
docker ps -a

# Остановка контейнера
docker stop butler-bot

# Запуск остановленного контейнера
docker start butler-bot

# Перезапуск контейнера
docker restart butler-bot

# Удаление контейнера
docker rm butler-bot

# Принудительное удаление работающего контейнера
docker rm -f butler-bot
```

### Просмотр логов

```bash
# Просмотр логов
docker logs butler-bot

# Последние 50 строк логов
docker logs butler-bot --tail 50

# Просмотр логов в реальном времени
docker logs -f butler-bot

# Логи с временными метками
docker logs -t butler-bot
```

### Работа с контейнером

```bash
# Вход в контейнер
docker exec -it butler-bot /bin/bash

# Выполнение команды в контейнере
docker exec butler-bot ps aux

# Просмотр переменных окружения
docker exec butler-bot env

# Работа с базой данных
docker exec -it butler-bot sqlite3 /app/data/butler_bot.db
```

## Работа с данными

### Резервное копирование

```bash
# Копирование базы данных из контейнера
docker cp butler-bot:/app/data/butler_bot.db ./backup_$(date +%Y%m%d_%H%M%S).db

# Резервное копирование через volume
docker run --rm \
  -v butler-data:/data \
  -v $(pwd):/backup \
  ubuntu:20.04 \
  cp /data/butler_bot.db /backup/butler_backup_$(date +%Y%m%d_%H%M%S).db
```

### Восстановление

```bash
# Восстановление базы данных в контейнер
docker cp backup_file.db butler-bot:/app/data/butler_bot.db

# Восстановление через volume
docker run --rm \
  -v butler-data:/data \
  -v $(pwd):/backup \
  ubuntu:20.04 \
  cp /backup/backup_file.db /data/butler_bot.db
```

### Просмотр содержимого volume

```bash
# Список файлов в volume
docker run --rm \
  -v butler-data:/data \
  ubuntu:20.04 \
  ls -la /data
```

## Обновление

### Полное обновление

```bash
# Остановка и удаление контейнера
docker stop butler-bot
docker rm butler-bot

# Пересборка образа
docker build -t butler-bot:latest .

# Запуск нового контейнера
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
```

### Обновление кода без потери данных

```bash
# Скрипт для автоматического обновления
cat > update.sh << 'EOF'
#!/bin/bash
echo "Обновление Butler Bot..."
docker stop butler-bot
docker rm butler-bot
docker build -t butler-bot:latest .
docker run -d \
  --name butler-bot \
  --restart unless-stopped \
  -v butler-data:/app/data \
  --env-file .env \
  butler-bot:latest
echo "Обновление завершено!"
EOF

chmod +x update.sh
./update.sh
```

## Мониторинг

### Статистика ресурсов

```bash
# Просмотр использования ресурсов
docker stats butler-bot

# Информация о контейнере
docker inspect butler-bot

# Информация об образе
docker inspect butler-bot:latest
```

### Проверка работоспособности

```bash
# Проверка, что контейнер работает
docker ps | grep butler-bot

# Проверка последних логов
docker logs butler-bot --tail 10

# Проверка переменных окружения
docker exec butler-bot env | grep TOKEN
```

## Устранение неполадок

### Очистка Docker

```bash
# Остановка всех контейнеров
docker stop $(docker ps -aq)

# Удаление всех остановленных контейнеров
docker container prune

# Удаление неиспользуемых образов
docker image prune

# Удаление всех неиспользуемых ресурсов
docker system prune

# Принудительная очистка всего
docker system prune -a --volumes
```

### Проблемы с правами

```bash
# Если проблемы с правами на файлы
sudo chown -R $USER:$USER .

# Проверка прав на Docker socket
sudo chmod 666 /var/run/docker.sock
```

### Проблемы с сетью

```bash
# Проверка сетевого подключения из контейнера
docker exec butler-bot ping -c 4 google.com

# Проверка DNS
docker exec butler-bot nslookup google.com
```

## Полезные алиасы

Добавьте в ~/.bashrc для удобства:

```bash
# Алиасы для Butler Bot
alias bb-logs='docker logs -f butler-bot'
alias bb-status='docker ps | grep butler-bot'
alias bb-restart='docker restart butler-bot'
alias bb-stop='docker stop butler-bot'
alias bb-start='docker start butler-bot'
alias bb-shell='docker exec -it butler-bot /bin/bash'
alias bb-stats='docker stats butler-bot --no-stream'
```

После добавления выполните:
```bash
source ~/.bashrc
```

## Скрипты автоматизации

### Скрипт мониторинга

```bash
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== Butler Bot Status ==="
    docker ps | grep butler-bot
    echo ""
    echo "=== Last 10 log lines ==="
    docker logs butler-bot --tail 10
    echo ""
    echo "=== Resource usage ==="
    docker stats butler-bot --no-stream
    sleep 30
done
EOF

chmod +x monitor.sh
```

### Скрипт резервного копирования

```bash
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/butler-bot-backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/butler_backup_$TIMESTAMP.db"

docker cp butler-bot:/app/data/butler_bot.db "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup created: $BACKUP_FILE"
    # Удаление старых бэкапов (старше 7 дней)
    find "$BACKUP_DIR" -name "butler_backup_*.db" -mtime +7 -delete
else
    echo "Backup failed!"
    exit 1
fi
EOF

chmod +x backup.sh
```

## Автоматическое обслуживание

### Cron задачи

Добавьте в crontab (`crontab -e`):

```bash
# Резервное копирование каждый день в 2:00
0 2 * * * /home/user/butler-bot/backup.sh

# Перезапуск контейнера каждую неделю в воскресенье в 3:00
0 3 * * 0 /usr/bin/docker restart butler-bot

# Очистка логов каждый месяц
0 4 1 * * /usr/bin/docker system prune -f
```

Эти команды помогут вам эффективно управлять Butler Bot на вашем Linux сервере!
