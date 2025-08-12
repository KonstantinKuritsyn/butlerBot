"""
Butler Bot - персональный помощник для ежедневных дел

Основные функции:
- 🌤️ Персональные уведомления о погоде в настраиваемое время
- 📅 Управление ежедневными задачами с напоминаниями
- ⏰ Разовые напоминания с системой повторов
- ⚙️ Персональные настройки для каждого пользователя
- 🗑️ Удаление и управление задачами через удобный интерфейс

Автор: AI Assistant
Версия: 2.0 с персональными настройками
"""
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from telegram import Update
from telegram.error import TelegramError
import datetime
import pytz
import os
import sqlite3
from dotenv import load_dotenv

from weather import WeatherService
from database import Database
from reminders import ReminderManager
from keyboard_utils import KeyboardBuilder

# Загружаем переменные окружения
load_dotenv()

# Константы
TIMEZONE = pytz.timezone('Europe/Moscow')
DEFAULT_WEATHER_TIME = '08:30'
CHECK_INTERVAL = 60  # секунды
MAX_REMINDERS = 10

# Инициализация сервисов
weather_service = WeatherService()
db = Database()
reminder_manager = ReminderManager()

# Состояния пользователя для многошаговых диалогов
user_states = {}

class UserState:
    NONE = "none"
    ADDING_DAILY_TASK_NAME = "adding_daily_task_name"
    ADDING_DAILY_TASK_TIME = "adding_daily_task_time"
    ADDING_ONE_TIME_TASK_NAME = "adding_one_time_task_name"
    ADDING_ONE_TIME_TASK_DATE = "adding_one_time_task_date"
    ADDING_ONE_TIME_TASK_TIME = "adding_one_time_task_time"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Добавляем пользователя в базу данных
    db.add_user(user.id, user.username, user.first_name)
    
    welcome_message = f"""🤖 *Привет, {user.first_name}!*

Я твой персональный Дворецкий! Вот что я умею:

🌤️ *Погода*
• Каждое утро в 8:30 присылаю прогноз погоды в Нижнем Новгороде
• Рекомендую, какую одежду лучше надеть

📅 *Ежедневные дела*
• Напоминаю о регулярных задачах
• Настраиваемое время напоминаний

⏰ *Разовые напоминания*
• Напоминаю о важных событиях в конкретную дату и время
• Система повторных напоминаний, если ты забыл

*Команды:*
/help - показать это сообщение
/add\\_daily - добавить ежедневное дело
/add\\_reminder - добавить разовое напоминание
/my\\_tasks - посмотреть все мои дела
/weather - получить текущую погоду

Готов помочь! 😊"""
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=KeyboardBuilder.main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """🆘 *Справка по командам*

*🌤️ Погода:*
/weather - получить текущую погоду

*📅 Управление задачами:*
/add\\_daily - добавить ежедневное дело
/add\\_reminder - добавить разовое напоминание
/my\\_tasks - посмотреть все дела

*⚙️ Другое:*
/help - показать эту справку
/start - перезапустить бота

*📝 Как работают напоминания:*
• Если ты не отметил задачу как выполненную, я буду напоминать снова
• Интервалы: через час → 30 мин → 15 мин → 10 мин → 5 мин
• Максимум 10 напоминаний

*Примеры:*
• Ежедневная задача: "Почистить зубы в 22:00"
• Разовое напоминание: "Позвонить в фитнес зал 10.08.2025 в 14:00"

Нужна помощь? Просто напиши мне! 😊"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /weather"""
    await update.message.reply_text("🌤️ Получаю данные о погоде...")
    
    weather_message = weather_service.format_weather_message()
    await update.message.reply_text(weather_message, parse_mode='Markdown')

async def add_daily_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_daily"""
    user_id = update.effective_user.id
    user_states[user_id] = UserState.ADDING_DAILY_TASK_NAME
    
    await update.message.reply_text(
        "📅 *Добавление ежедневного дела*\n\n"
        "Введите название задачи (например: 'Почистить зубы'):",
        parse_mode='Markdown'
    )

async def add_one_time_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_reminder"""
    user_id = update.effective_user.id
    user_states[user_id] = UserState.ADDING_ONE_TIME_TASK_NAME
    
    await update.message.reply_text(
        "⏰ *Добавление разового напоминания*\n\n"
        "Введите название задачи (например: 'Позвонить в фитнес зал'):",
        parse_mode='Markdown'
    )

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /my_tasks"""
    user_id = update.effective_user.id
    
    # Получаем ежедневные задачи
    daily_tasks = db.get_user_daily_tasks(user_id)
    one_time_tasks = db.get_user_one_time_tasks(user_id)
    
    message = "📋 *Ваши задачи:*\n\n"
    
    if daily_tasks:
        message += "📅 *Ежедневные дела:*\n"
        for task in daily_tasks:
            message += f"• {task['task_name']} - {task['time']}\n"
        message += "\n"
    
    if one_time_tasks:
        message += "⏰ *Разовые напоминания:*\n"
        for task in one_time_tasks:
            dt = datetime.datetime.fromisoformat(task['scheduled_datetime'])
            formatted_dt = dt.strftime("%d.%m.%Y в %H:%M")
            message += f"• {task['task_name']} - {formatted_dt}\n"
        message += "\n"
    
    if not daily_tasks and not one_time_tasks:
        message += "У вас пока нет задач.\n\n"
        message += "Используйте кнопки ниже для добавления задач!"
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=KeyboardBuilder.tasks_menu(daily_tasks, one_time_tasks)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений в зависимости от состояния пользователя"""
    user_id = update.effective_user.id
    text = update.message.text
    
    state = user_states.get(user_id, UserState.NONE)
    
    if state == UserState.ADDING_DAILY_TASK_NAME:
        # Сохраняем название задачи и просим время
        context.user_data['daily_task_name'] = text
        user_states[user_id] = UserState.ADDING_DAILY_TASK_TIME
        
        await update.message.reply_text(
            f"✅ Задача: '{text}'\n\n"
            "Теперь введите время напоминания (например: 22:00 или 8.30):",
            parse_mode='Markdown'
        )
    
    elif state == UserState.ADDING_DAILY_TASK_TIME:
        # Обрабатываем время и сохраняем задачу
        time_str = reminder_manager.parse_time_input(text)
        
        if not time_str:
            await update.message.reply_text(
                "❌ Неверный формат времени. Попробуйте еще раз (например: 22:00 или 8.30):"
            )
            return
        
        task_name = context.user_data.get('daily_task_name')
        task_id = db.add_daily_task(user_id, task_name, time_str)
        
        user_states[user_id] = UserState.NONE
        context.user_data.pop('daily_task_name', None)
        
        await update.message.reply_text(
            f"✅ *Ежедневная задача добавлена!*\n\n"
            f"📝 {task_name}\n"
            f"⏰ Каждый день в {time_str}\n\n"
            f"Я буду напоминать вам об этом каждый день!",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.main_menu()
        )
    
    elif state == UserState.ADDING_ONE_TIME_TASK_NAME:
        # Сохраняем название и просим дату
        context.user_data['one_time_task_name'] = text
        user_states[user_id] = UserState.ADDING_ONE_TIME_TASK_DATE
        
        await update.message.reply_text(
            f"✅ Задача: '{text}'\n\n"
            "Введите дату (например: 10.08.2025 или 15/12/2024):",
            parse_mode='Markdown'
        )
    
    elif state == UserState.ADDING_ONE_TIME_TASK_DATE:
        # Сохраняем дату и просим время
        context.user_data['one_time_task_date'] = text
        user_states[user_id] = UserState.ADDING_ONE_TIME_TASK_TIME
        
        await update.message.reply_text(
            f"✅ Дата: {text}\n\n"
            "Введите время (например: 14:00 или 9.30):",
            parse_mode='Markdown'
        )
    
    elif state == UserState.ADDING_ONE_TIME_TASK_TIME:
        # Обрабатываем время и сохраняем задачу
        task_name = context.user_data.get('one_time_task_name')
        date_text = context.user_data.get('one_time_task_date')
        
        target_datetime = reminder_manager.parse_datetime_input(date_text, text)
        
        if not target_datetime:
            await update.message.reply_text(
                "❌ Неверный формат времени или дата уже прошла. "
                "Попробуйте еще раз (например: 14:00):"
            )
            return
        
        task_id = db.add_one_time_task(user_id, task_name, target_datetime)
        
        user_states[user_id] = UserState.NONE
        context.user_data.pop('one_time_task_name', None)
        context.user_data.pop('one_time_task_date', None)
        
        formatted_dt = target_datetime.strftime("%d.%m.%Y в %H:%M")
        await update.message.reply_text(
            f"✅ *Напоминание добавлено!*\n\n"
            f"📝 {task_name}\n"
            f"📅 {formatted_dt}\n\n"
            f"Я напомню вам об этом в указанное время!",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.main_menu()
        )
    
    else:
        # Обычное сообщение
        await update.message.reply_text(
            "Я не понимаю эту команду 🤔\n\n"
            "Используйте /help для просмотра доступных команд."
        )

async def handle_action_callback(query, action):
    """Обработка action кнопок (главное меню, навигация)"""
    user_id = query.from_user.id
    
    if action == "main_menu":
        await query.edit_message_text(
            "🏠 *Главное меню*\n\nВыберите действие:",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.main_menu()
        )
    
    elif action == "weather":
        await query.edit_message_text("🌤️ Получаю данные о погоде...")
        weather_message = weather_service.format_weather_message()
        await query.edit_message_text(
            weather_message, 
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_to_menu()
        )
    
    elif action == "my_tasks":
        daily_tasks = db.get_user_daily_tasks(user_id)
        one_time_tasks = db.get_user_one_time_tasks(user_id)
        
        message = "📋 *Ваши задачи:*\n\n"
        
        if daily_tasks:
            message += "📅 *Ежедневные дела:*\n"
            for task in daily_tasks:
                message += f"• {task['task_name']} - {task['time']}\n"
            message += "\n"
        
        if one_time_tasks:
            message += "⏰ *Разовые напоминания:*\n"
            for task in one_time_tasks:
                dt = datetime.datetime.fromisoformat(task['scheduled_datetime'])
                formatted_dt = dt.strftime("%d.%m.%Y в %H:%M")
                message += f"• {task['task_name']} - {formatted_dt}\n"
            message += "\n"
        
        if not daily_tasks and not one_time_tasks:
            message += "У вас пока нет задач.\n\n"
            message += "Используйте кнопки ниже для добавления задач!"
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.tasks_menu(daily_tasks, one_time_tasks)
        )
    
    elif action == "add_daily":
        user_states[user_id] = UserState.ADDING_DAILY_TASK_NAME
        await query.edit_message_text(
            "📅 *Добавление ежедневного дела*\n\n"
            "Введите название задачи (например: 'Почистить зубы'):",
            parse_mode='Markdown'
        )
    
    elif action == "add_reminder":
        user_states[user_id] = UserState.ADDING_ONE_TIME_TASK_NAME
        await query.edit_message_text(
            "⏰ *Добавление разового напоминания*\n\n"
            "Введите название задачи (например: 'Позвонить в фитнес зал'):",
            parse_mode='Markdown'
        )
    
    elif action == "help":
        help_text = """🆘 *Справка по командам*

*🌤️ Погода:*
/weather - получить текущую погоду

*📅 Управление задачами:*
/add\\_daily - добавить ежедневное дело
/add\\_reminder - добавить разовое напоминание
/my\\_tasks - посмотреть все дела

*⚙️ Другое:*
/help - показать эту справку
/start - перезапустить бота

*📝 Как работают напоминания:*
• Если ты не отметил задачу как выполненную, я буду напоминать снова
• Интервалы: через час → 30 мин → 15 мин → 10 мин → 5 мин
• Максимум 10 напоминаний

*Примеры:*
• Ежедневная задача: "Почистить зубы в 22:00"
• Разовое напоминание: "Позвонить в фитнес зал 10.08.2025 в 14:00"

Нужна помощь? Просто напиши мне! 😊"""
        
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_to_menu()
        )
    
    elif action == "settings":
        settings = db.get_user_weather_settings(user_id)
        await query.edit_message_text(
            "⚙️ *Настройки*\n\n"
            "Здесь вы можете настроить уведомления о погоде:",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.settings_menu(
                settings['notifications_enabled'],
                settings['weather_time']
            )
        )

async def handle_manage_callback(query, list_type):
    """Обработка manage кнопок (управление списками задач)"""
    user_id = query.from_user.id
    
    if list_type == "daily_tasks":
        tasks = db.get_user_daily_tasks(user_id)
        if tasks:
            await query.edit_message_text(
                "📅 *Управление ежедневными делами*\n\n"
                "Выберите задачу для просмотра или удаления:",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.daily_tasks_list(tasks)
            )
        else:
            await query.edit_message_text(
                "📅 У вас нет ежедневных дел.",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.back_to_menu()
            )
    
    elif list_type == "one_time_tasks":
        tasks = db.get_user_one_time_tasks(user_id)
        if tasks:
            await query.edit_message_text(
                "⏰ *Управление напоминаниями*\n\n"
                "Выберите напоминание для просмотра или удаления:",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.one_time_tasks_list(tasks)
            )
        else:
            await query.edit_message_text(
                "⏰ У вас нет разовых напоминаний.",
                parse_mode='Markdown',
                reply_markup=KeyboardBuilder.back_to_menu()
            )

async def handle_view_task_callback(query, task_type, task_id):
    """Обработка просмотра конкретной задачи"""
    user_id = query.from_user.id
    
    if task_type == "daily":
        tasks = db.get_user_daily_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if task:
            message = f"📅 *Ежедневное дело*\n\n" \
                     f"📝 *Название:* {task['task_name']}\n" \
                     f"⏰ *Время:* {task['time']}\n" \
                     f"📅 *Создано:* {task['created_at']}"
        else:
            message = "❌ Задача не найдена."
    
    elif task_type == "one_time":
        tasks = db.get_user_one_time_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if task:
            dt = datetime.datetime.fromisoformat(task['scheduled_datetime'])
            formatted_dt = dt.strftime("%d.%m.%Y в %H:%M")
            message = f"⏰ *Разовое напоминание*\n\n" \
                     f"📝 *Название:* {task['task_name']}\n" \
                     f"📅 *Дата и время:* {formatted_dt}\n" \
                     f"📅 *Создано:* {task['created_at']}"
        else:
            message = "❌ Напоминание не найдено."
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=KeyboardBuilder.task_detail_menu(task_id, task_type)
    )

async def handle_delete_callback(query, task_type, task_id):
    """Обработка запроса на удаление задачи"""
    user_id = query.from_user.id
    
    # Получаем название задачи для подтверждения
    if task_type == "daily":
        tasks = db.get_user_daily_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        task_name = task['task_name'] if task else "Неизвестная задача"
        type_name = "ежедневное дело"
    else:
        tasks = db.get_user_one_time_tasks(user_id)
        task = next((t for t in tasks if t['id'] == task_id), None)
        task_name = task['task_name'] if task else "Неизвестное напоминание"
        type_name = "разовое напоминание"
    
    message = f"🗑️ *Удаление*\n\n" \
             f"Вы уверены, что хотите удалить {type_name}?\n\n" \
             f"📝 *{task_name}*"
    
    await query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=KeyboardBuilder.confirm_delete(task_id, task_type)
    )

async def handle_confirm_delete_callback(query, task_type, task_id):
    """Обработка подтверждения удаления задачи"""
    user_id = query.from_user.id
    
    try:
        if task_type == "daily":
            db.delete_daily_task(task_id)
            message = "✅ Ежедневное дело успешно удалено!"
        else:
            db.delete_one_time_task(task_id)
            message = "✅ Разовое напоминание успешно удалено!"
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_to_menu()
        )
    
    except Exception as e:
        await query.edit_message_text(
            "❌ Ошибка при удалении задачи. Попробуйте еще раз.",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_to_menu()
        )

async def handle_toggle_callback(query, setting_type):
    """Обработка переключения настроек"""
    user_id = query.from_user.id
    
    if setting_type == "weather_notifications":
        new_state = db.toggle_weather_notifications(user_id)
        settings = db.get_user_weather_settings(user_id)
        
        status = "включены" if new_state else "выключены"
        message = f"🌤️ Уведомления о погоде {status}!"
        
        await query.edit_message_text(
            f"⚙️ *Настройки*\n\n{message}\n\n"
            "Здесь вы можете настроить уведомления о погоде:",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.settings_menu(
                settings['notifications_enabled'],
                settings['weather_time']
            )
        )

async def handle_set_callback(query, setting_type):
    """Обработка настройки параметров"""
    user_id = query.from_user.id
    
    if setting_type == "weather_time":
        await query.edit_message_text(
            "⏰ *Выберите время для получения погоды:*\n\n"
            "Погода будет приходить каждый день в выбранное время.",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.weather_time_menu()
        )

async def handle_set_time_callback(query, time_str):
    """Обработка установки времени погоды"""
    user_id = query.from_user.id
    
    try:
        db.update_user_weather_time(user_id, time_str)
        settings = db.get_user_weather_settings(user_id)
        
        await query.edit_message_text(
            f"⚙️ *Настройки*\n\n"
            f"✅ Время получения погоды изменено на {time_str}!\n\n"
            "Здесь вы можете настроить уведомления о погоде:",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.settings_menu(
                settings['notifications_enabled'],
                settings['weather_time']
            )
        )
    except Exception as e:
        await query.edit_message_text(
            "❌ Ошибка при сохранении настроек. Попробуйте еще раз.",
            parse_mode='Markdown',
            reply_markup=KeyboardBuilder.back_to_menu()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    parts = data.split("|")
    
    # Обработка action кнопок (главное меню, навигация)
    if len(parts) == 2 and parts[0] == "action":
        await handle_action_callback(query, parts[1])
        return
    
    # Обработка manage кнопок (управление списками задач)
    elif len(parts) == 2 and parts[0] == "manage":
        await handle_manage_callback(query, parts[1])
        return
    
    # Обработка view кнопок (просмотр конкретной задачи)
    elif len(parts) == 2 and parts[0].startswith("view_"):
        task_type = parts[0].replace("view_", "")
        task_id = int(parts[1])
        await handle_view_task_callback(query, task_type, task_id)
        return
    
    # Обработка delete кнопок
    elif len(parts) == 3 and parts[0] == "delete":
        task_type = parts[1]
        task_id = int(parts[2])
        await handle_delete_callback(query, task_type, task_id)
        return
    
    # Обработка confirm_delete кнопок
    elif len(parts) == 3 and parts[0] == "confirm_delete":
        task_type = parts[1]
        task_id = int(parts[2])
        await handle_confirm_delete_callback(query, task_type, task_id)
        return
    
    # Обработка toggle кнопок (переключения настроек)
    elif len(parts) == 2 and parts[0] == "toggle":
        await handle_toggle_callback(query, parts[1])
        return
    
    # Обработка set кнопок (настройка времени)
    elif len(parts) == 2 and parts[0] == "set":
        await handle_set_callback(query, parts[1])
        return
    
    # Обработка set_time кнопок (установка конкретного времени)
    elif len(parts) == 2 and parts[0] == "set_time":
        await handle_set_time_callback(query, parts[1])
        return
    
    # Обработка напоминаний (старый формат)
    elif len(parts) == 4:
        try:
            action = parts[0]  # complete или snooze
            task_type = parts[1]  # daily или one_time
            task_id = int(parts[2])
            reminder_id = int(parts[3])
        except ValueError as e:
            await query.edit_message_text(
                "❌ Ошибка обработки команды. Попробуйте еще раз.",
                parse_mode='Markdown'
            )
            return
        
        if action == "complete":
            # Отмечаем задачу как выполненную
            db.complete_reminder(reminder_id)
            
            if task_type == "one_time":
                db.complete_one_time_task(task_id)
            
            await query.edit_message_text(
                f"✅ *Отлично!* Задача отмечена как выполненная.\n\n"
                f"{query.message.text.split('📝')[1] if '📝' in query.message.text else 'Задача'}",
                parse_mode='Markdown'
            )
        
        elif action == "snooze":
            # Откладываем напоминание
            next_reminder_time = reminder_manager.get_next_reminder_time(1)  # Начинаем с 1 часа
            
            if next_reminder_time:
                db.update_reminder_history(reminder_id, next_reminder_time)
                time_str = next_reminder_time.strftime("%H:%M")
                
                await query.edit_message_text(
                    f"⏱️ *Напоминание отложено*\n\n"
                    f"Я напомню снова в {time_str}",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ Больше нельзя откладывать это напоминание.",
                    parse_mode='Markdown'
                )
    else:
        # Если формат callback_data неправильный
        await query.edit_message_text(
            "❌ Неизвестная команда.",
            parse_mode='Markdown'
        )

async def send_weather_notification_for_time(context: ContextTypes.DEFAULT_TYPE):
    """Отправка персонализированных уведомлений о погоде"""
    current_time = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
    users = db.get_users_for_weather_time(current_time)
    
    if not users:
        return
    
    weather_message = weather_service.format_weather_message()
    
    for user in users:
        try:
            greeting = get_time_greeting(current_time)
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"{greeting}\n\n{weather_message}",
                parse_mode='Markdown'
            )
        except TelegramError as e:
            print(f"Ошибка отправки погоды пользователю {user['user_id']}: {e}")

def get_time_greeting(time_str: str) -> str:
    """Возвращает приветствие в зависимости от времени"""
    hour = int(time_str.split(':')[0])
    
    if 5 <= hour < 12:
        return "🌅 *Доброе утро!*"
    elif 12 <= hour < 17:
        return "☀️ *Добрый день!*"
    elif 17 <= hour < 22:
        return "🌆 *Добрый вечер!*"
    else:
        return "🌙 *Доброй ночи!*"

async def check_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Проверка ежедневных задач"""
    current_time = datetime.datetime.now(TIMEZONE).strftime("%H:%M")
    tasks = db.get_tasks_for_time(current_time)
    
    for task in tasks:
        try:
            message = f"⏰ *Напоминание:*\n\n📝 {task['task_name']}"
            
            # Добавляем запись в историю напоминаний
            next_reminder = reminder_manager.get_next_reminder_time(1)
            reminder_id = db.add_reminder_history(
                task['user_id'], 'daily', task['task_id'], 
                datetime.datetime.now(), next_reminder
            )
            
            # Создаем keyboard с правильным reminder_id
            keyboard = reminder_manager.get_reminder_keyboard_markup(
                task['task_id'], 'daily', reminder_id
            )
            
            await context.bot.send_message(
                chat_id=task['user_id'],
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            print(f"Ошибка отправки напоминания пользователю {task['user_id']}: {e}")

async def check_one_time_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Проверка одноразовых задач"""
    current_datetime = datetime.datetime.now(TIMEZONE)
    tasks = db.get_one_time_tasks_for_time(current_datetime)
    
    for task in tasks:
        try:
            message = f"⏰ *Напоминание:*\n\n📝 {task['task_name']}"
            
            # Добавляем запись в историю напоминаний
            next_reminder = reminder_manager.get_next_reminder_time(1)
            reminder_id = db.add_reminder_history(
                task['user_id'], 'one_time', task['task_id'], 
                datetime.datetime.now(), next_reminder
            )
            
            # Создаем keyboard с правильным reminder_id
            keyboard = reminder_manager.get_reminder_keyboard_markup(
                task['task_id'], 'one_time', reminder_id
            )
            
            await context.bot.send_message(
                chat_id=task['user_id'],
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            print(f"Ошибка отправки напоминания пользователю {task['user_id']}: {e}")

async def check_pending_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Проверка отложенных напоминаний"""
    reminders = db.get_pending_reminders()
    
    for reminder in reminders:
        try:
            # Получаем информацию о задаче
            if reminder['task_type'] == 'daily':
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT task_name FROM daily_tasks WHERE id = ?",
                        (reminder['task_id'],)
                    )
                    result = cursor.fetchone()
                    task_name = result[0] if result else "Неизвестная задача"
            else:
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT task_name FROM one_time_tasks WHERE id = ?",
                        (reminder['task_id'],)
                    )
                    result = cursor.fetchone()
                    task_name = result[0] if result else "Неизвестная задача"
            
            # Форматируем сообщение
            message = reminder_manager.format_reminder_message(
                task_name, reminder['reminder_count']
            )
            
            # Получаем время следующего напоминания
            next_reminder = reminder_manager.get_next_reminder_time(
                reminder['reminder_count'] + 1
            )
            
            # Обновляем историю
            db.update_reminder_history(reminder['id'], next_reminder)
            
            # Отправляем напоминание
            keyboard = reminder_manager.get_reminder_keyboard_markup(
                reminder['task_id'], reminder['task_type'], reminder['id']
            )
            
            await context.bot.send_message(
                chat_id=reminder['user_id'],
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            print(f"Ошибка отправки повторного напоминания: {e}")

def main():
    """Основная функция запуска бота"""
    app = ApplicationBuilder().token(os.environ.get('TELEGRAM_TOKEN_WISH_BOT')).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("add_daily", add_daily_task))
    app.add_handler(CommandHandler("add_reminder", add_one_time_reminder))
    app.add_handler(CommandHandler("my_tasks", my_tasks))
    
    # Обработчики сообщений и callback'ов
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Планировщик задач
    job_queue = app.job_queue
    
    # Проверка персональных уведомлений о погоде каждую минуту
    job_queue.run_repeating(
        send_weather_notification_for_time,
        interval=60,
        name="weather_notifications"
    )
    
    # Проверка задач каждую минуту
    job_queue.run_repeating(
        check_daily_tasks,
        interval=60,
        name="check_daily_tasks"
    )
    
    job_queue.run_repeating(
        check_one_time_tasks,
        interval=60,
        name="check_one_time_tasks"
    )
    
    job_queue.run_repeating(
        check_pending_reminders,
        interval=60,
        name="check_pending_reminders"
    )
    
    print("🤖 Butler Bot запущен...")
    print("🌤️ Погода: персональные настройки времени")
    print("📅 Проверка задач: каждую минуту")
    print("⏰ Проверка напоминаний: каждую минуту")
    print("⚙️ Персональные настройки: доступны")
    
    app.run_polling()

if __name__ == '__main__':
    main()
