"""
Модуль для управления напоминаниями и повторами
"""
import datetime
from typing import Optional

class ReminderManager:
    def __init__(self):
        # Интервалы повторов в минутах: час, полчаса, 15 минут, 10 минут, 5 минут
        self.reminder_intervals = [60, 30, 15, 10, 5]
    
    def get_next_reminder_time(self, reminder_count: int) -> Optional[datetime.datetime]:
        """Возвращает время следующего напоминания"""
        if reminder_count <= 0:
            return None
            
        # Определяем интервал на основе количества напоминаний
        if reminder_count <= len(self.reminder_intervals):
            interval_minutes = self.reminder_intervals[reminder_count - 1]
        else:
            # После всех интервалов напоминаем каждые 5 минут
            interval_minutes = 5
        
        # Максимум 10 напоминаний
        if reminder_count >= 10:
            return None
            
        return datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes)
    
    def format_reminder_message(self, task_name: str, reminder_count: int, 
                               task_type: str = "task") -> str:
        """Форматирует сообщение напоминания"""
        
        if reminder_count == 1:
            prefix = "⏰ Напоминание:"
        elif reminder_count <= 3:
            prefix = f"⏰ Повторное напоминание ({reminder_count}):"
        else:
            prefix = f"🔔 Срочное напоминание ({reminder_count}):"
        
        message = f"{prefix}\n\n📝 {task_name}"
        
        if reminder_count >= 5:
            message += f"\n\n❗ Это уже {reminder_count}-е напоминание!"
        
        return message
    
    def get_reminder_keyboard_markup(self, task_id: int, task_type: str, reminder_id: int):
        """Возвращает клавиатуру для напоминания"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Уже сделал", 
                    callback_data=f"complete|{task_type}|{task_id}|{reminder_id}"
                ),
                InlineKeyboardButton(
                    "⏱️ Напомнить позже", 
                    callback_data=f"snooze|{task_type}|{task_id}|{reminder_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def format_task_time(self, time_str: str) -> str:
        """Форматирует время для отображения"""
        try:
            if ":" in time_str:
                hour, minute = time_str.split(":")
                return f"{hour:0>2}:{minute:0>2}"
            return time_str
        except:
            return time_str
    
    def parse_time_input(self, time_input: str) -> Optional[str]:
        """Парсит введенное пользователем время"""
        try:
            # Убираем лишние пробелы
            time_input = time_input.strip()
            
            # Если есть точка, заменяем на двоеточие
            time_input = time_input.replace(".", ":")
            
            # Проверяем различные форматы
            if ":" in time_input:
                parts = time_input.split(":")
                if len(parts) == 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                else:
                    return None
            else:
                # Только час
                hour = int(time_input)
                minute = 0
            
            # Валидация
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def parse_datetime_input(self, date_input: str, time_input: str) -> Optional[datetime.datetime]:
        """Парсит введенные пользователем дату и время"""
        try:
            # Парсим время
            time_str = self.parse_time_input(time_input)
            if not time_str:
                return None
            
            hour, minute = map(int, time_str.split(":"))
            
            # Парсим дату
            date_input = date_input.strip()
            
            # Различные форматы даты
            date_formats = [
                "%d.%m.%Y",    # 10.08.2025
                "%d/%m/%Y",    # 10/08/2025
                "%d-%m-%Y",    # 10-08-2025
                "%d.%m.%y",    # 10.08.25
                "%d/%m/%y",    # 10/08/25
                "%d-%m-%y",    # 10-08-25
            ]
            
            target_date = None
            for date_format in date_formats:
                try:
                    target_date = datetime.datetime.strptime(date_input, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not target_date:
                return None
            
            # Создаем datetime объект
            target_datetime = datetime.datetime.combine(
                target_date, 
                datetime.time(hour, minute)
            )
            
            # Проверяем, что дата в будущем
            if target_datetime <= datetime.datetime.now():
                return None
                
            return target_datetime
            
        except Exception:
            return None
