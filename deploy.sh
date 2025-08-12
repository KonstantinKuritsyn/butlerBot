#!/bin/bash

# Скрипт автоматического развертывания Butler Bot на Linux сервере
# Использование: bash deploy.sh

set -e

echo "🤖 Скрипт развертывания Butler Bot"
echo "=================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для цветного вывода
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка установки Docker
check_docker() {
    print_step "Проверка установки Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker и запустите скрипт снова."
        echo "Инструкции по установке: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker не запущен или нет прав доступа."
        echo "Запустите: sudo systemctl start docker"
        echo "Добавьте пользователя в группу: sudo usermod -aG docker \$USER"
        exit 1
    fi
    
    print_status "Docker установлен и работает"
}

# Создание рабочей директории
create_directory() {
    print_step "Проверка рабочей директории..."
    CURRENT_DIR=$(pwd)
    print_status "Рабочая директория: $CURRENT_DIR"
}

# Создание файла .env
create_env_file() {
    print_step "Создание файла .env..."
    
    if [ -f .env ]; then
        print_warning "Файл .env уже существует. Оставляем существующий."
        return
    fi
    
    echo "Введите Telegram Bot Token (от @BotFather):"
    read -r TELEGRAM_TOKEN
    
    echo "Введите WeatherAPI Token (от weatherapi.com):"
    read -r WEATHER_TOKEN
    
    cat > .env << EOF
# Telegram Bot Token
TELEGRAM_TOKEN_WISH_BOT=${TELEGRAM_TOKEN}

# Weather API Token
WEATHER_API_TOKEN=${WEATHER_TOKEN}
EOF
    
    print_status "Файл .env создан"
}

# Создание Dockerfile
create_dockerfile() {
    print_step "Проверка Dockerfile..."
    
    if [ -f Dockerfile ]; then
        print_warning "Dockerfile уже существует. Оставляем существующий."
        return
    fi
    
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
    
    print_status "Dockerfile создан"
}

# Создание requirements.txt
create_requirements() {
    print_step "Проверка requirements.txt..."
    
    if [ -f requirements.txt ]; then
        print_warning "requirements.txt уже существует. Оставляем существующий."
        return
    fi
    
    cat > requirements.txt << 'EOF'
python-telegram-bot[job-queue]==20.7
pytz==2023.3
python-dotenv==1.0.0
requests==2.31.0
EOF
    
    print_status "requirements.txt создан"
}

# Проверка наличия исходных файлов
check_source_files() {
    print_step "Проверка исходных файлов..."
    
    required_files=("main.py" "database.py" "weather.py" "reminders.py" "keyboard_utils.py")
    missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        print_error "Отсутствуют следующие файлы:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Скопируйте исходные файлы в директорию ~/butler-bot"
        echo "Или используйте scp: scp file.py user@server:~/butler-bot/"
        exit 1
    fi
    
    print_status "Все исходные файлы найдены"
}

# Сборка Docker образа
build_image() {
    print_step "Сборка Docker образа..."
    
    docker build -t butler-bot:latest .
    
    if [ $? -eq 0 ]; then
        print_status "Docker образ успешно собран"
    else
        print_error "Ошибка при сборке Docker образа"
        exit 1
    fi
}

# Создание Docker volume
create_volume() {
    print_step "Создание Docker volume для данных..."
    
    if docker volume ls | grep -q butler-data; then
        print_warning "Volume butler-data уже существует"
    else
        docker volume create butler-data
        print_status "Volume butler-data создан"
    fi
}

# Остановка существующего контейнера
stop_existing_container() {
    if docker ps -a | grep -q butler-bot; then
        print_step "Остановка существующего контейнера..."
        docker stop butler-bot 2>/dev/null || true
        docker rm butler-bot 2>/dev/null || true
        print_status "Существующий контейнер удален"
    fi
}

# Запуск контейнера
start_container() {
    print_step "Запуск Butler Bot контейнера..."
    
    docker run -d \
        --name butler-bot \
        --restart unless-stopped \
        -v butler-data:/app/data \
        --env-file .env \
        butler-bot:latest
    
    if [ $? -eq 0 ]; then
        print_status "Butler Bot контейнер запущен"
    else
        print_error "Ошибка при запуске контейнера"
        exit 1
    fi
}

# Проверка работы
check_status() {
    print_step "Проверка статуса..."
    
    sleep 3
    
    if docker ps | grep -q butler-bot; then
        print_status "Контейнер работает"
        echo ""
        echo "Просмотр логов:"
        docker logs butler-bot --tail 10
        echo ""
        print_status "Развертывание завершено успешно! 🎉"
    else
        print_error "Контейнер не запущен"
        echo "Проверьте логи: docker logs butler-bot"
        exit 1
    fi
}

# Создание управляющих скриптов
create_management_scripts() {
    print_step "Создание управляющих скриптов..."
    
    # Скрипт для просмотра логов
    cat > view-logs.sh << 'EOF'
#!/bin/bash
echo "Логи Butler Bot (Ctrl+C для выхода):"
docker logs -f butler-bot
EOF
    
    # Скрипт для перезапуска
    cat > restart.sh << 'EOF'
#!/bin/bash
echo "Перезапуск Butler Bot..."
docker restart butler-bot
echo "Контейнер перезапущен"
EOF
    
    # Скрипт для остановки
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "Остановка Butler Bot..."
docker stop butler-bot
echo "Контейнер остановлен"
EOF
    
    # Скрипт для обновления
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
echo "Butler Bot обновлен и перезапущен"
EOF
    
    chmod +x view-logs.sh restart.sh stop.sh update.sh
    print_status "Управляющие скрипты созданы"
}

# Основная функция
main() {
    echo "Начинаем развертывание Butler Bot..."
    echo ""
    
    check_docker
    create_directory
    create_env_file
    create_dockerfile
    create_requirements
    check_source_files
    build_image
    create_volume
    stop_existing_container
    start_container
    check_status
    create_management_scripts
    
    echo ""
    echo "🎉 Развертывание завершено!"
    echo ""
    echo "Полезные команды:"
    echo "  Просмотр логов:    ./view-logs.sh"
    echo "  Перезапуск:        ./restart.sh"
    echo "  Остановка:         ./stop.sh"
    echo "  Обновление:        ./update.sh"
    echo ""
    echo "  Статус:            docker ps"
    echo "  Логи:              docker logs butler-bot"
    echo "  Вход в контейнер:  docker exec -it butler-bot /bin/bash"
    echo ""
}

# Запуск основной функции
main "$@"
