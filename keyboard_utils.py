"""
Модуль для создания клавиатур и интерфейса с кнопками
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import datetime

class KeyboardBuilder:
    
    @staticmethod
    def main_menu():
        """Главное меню с основными функциями"""
        keyboard = [
            [
                InlineKeyboardButton("🌤️ Погода", callback_data="action|weather"),
                InlineKeyboardButton("📋 Мои задачи", callback_data="action|my_tasks")
            ],
            [
                InlineKeyboardButton("➕ Ежедневное дело", callback_data="action|add_daily")
            ],
            [
                InlineKeyboardButton("⏰ Разовое напоминание", callback_data="action|add_reminder")
            ],
            [
                InlineKeyboardButton("❓ Справка", callback_data="action|help"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="action|settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def tasks_menu(daily_tasks=None, one_time_tasks=None):
        """Меню управления задачами"""
        keyboard = []
        
        # Кнопки управления ежедневными задачами
        if daily_tasks:
            keyboard.append([
                InlineKeyboardButton("📅 Управлять ежедневными", callback_data="manage|daily_tasks")
            ])
        
        # Кнопки управления разовыми задачами  
        if one_time_tasks:
            keyboard.append([
                InlineKeyboardButton("⏰ Управлять напоминаниями", callback_data="manage|one_time_tasks")
            ])
        
        # Кнопки добавления показываем только если нет задач
        if not daily_tasks and not one_time_tasks:
            keyboard.extend([
                [
                    InlineKeyboardButton("➕ Ежедневное дело", callback_data="action|add_daily")
                ],
                [
                    InlineKeyboardButton("⏰ Разовое напоминание", callback_data="action|add_reminder")
                ]
            ])
        
        # Кнопка главного меню всегда
        keyboard.append([
            InlineKeyboardButton("🏠 Главное меню", callback_data="action|main_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def daily_tasks_list(tasks):
        """Список ежедневных задач для управления"""
        keyboard = []
        
        for task in tasks:
            # Обрезаем длинные названия
            task_name = task['task_name']
            if len(task_name) > 20:
                task_name = task_name[:17] + "..."
            
            keyboard.append([
                InlineKeyboardButton(
                    f"📝 {task_name} ({task['time']})",
                    callback_data=f"view_daily|{task['id']}"
                )
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("➕ Добавить ещё", callback_data="action|add_daily")
            ],
            [
                InlineKeyboardButton("◀️ Назад к задачам", callback_data="action|my_tasks")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def one_time_tasks_list(tasks):
        """Список разовых задач для управления"""
        keyboard = []
        
        for task in tasks:
            # Обрезаем длинные названия
            task_name = task['task_name']
            if len(task_name) > 15:
                task_name = task_name[:12] + "..."
            
            try:
                dt = datetime.datetime.fromisoformat(task['scheduled_datetime'])
                formatted_dt = dt.strftime("%d.%m %H:%M")
                keyboard.append([
                    InlineKeyboardButton(
                        f"⏰ {task_name} ({formatted_dt})",
                        callback_data=f"view_one_time|{task['id']}"
                    )
                ])
            except:
                keyboard.append([
                    InlineKeyboardButton(
                        f"⏰ {task_name}",
                        callback_data=f"view_one_time|{task['id']}"
                    )
                ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("➕ Добавить ещё", callback_data="action|add_reminder")
            ],
            [
                InlineKeyboardButton("◀️ Назад к задачам", callback_data="action|my_tasks")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_detail_menu(task_id, task_type):
        """Меню действий для конкретной задачи"""
        keyboard = [
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete|{task_type}|{task_id}")
            ],
            [
                InlineKeyboardButton("◀️ Назад к списку", callback_data=f"manage|{task_type}_tasks")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_delete(task_id, task_type):
        """Подтверждение удаления задачи"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete|{task_type}|{task_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{task_type}|{task_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu(weather_enabled=True, weather_time="08:30"):
        """Меню настроек"""
        status_text = "🔔 Включены" if weather_enabled else "🔕 Выключены"
        keyboard = [
            [
                InlineKeyboardButton(f"🌤️ Погода: {status_text}", callback_data="toggle|weather_notifications")
            ],
            [
                InlineKeyboardButton(f"⏰ Время погоды: {weather_time}", callback_data="set|weather_time")
            ],
            [
                InlineKeyboardButton("🏠 Главное меню", callback_data="action|main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def weather_time_menu():
        """Меню выбора времени для погоды"""
        times = ["07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00"]
        keyboard = []
        
        # Разбиваем на строки по 2 кнопки
        for i in range(0, len(times), 2):
            row = []
            for j in range(i, min(i + 2, len(times))):
                row.append(InlineKeyboardButton(
                    times[j], 
                    callback_data=f"set_time|{times[j]}"
                ))
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад к настройкам", callback_data="action|settings")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu():
        """Простая кнопка возврата в главное меню"""
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="action|main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
