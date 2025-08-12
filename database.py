"""
Модуль для работы с базой данных
"""
import sqlite3
import datetime
import os
from typing import List, Dict

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Проверяем, запущены ли мы в Docker
            if os.path.exists('/app/data'):
                self.db_path = "/app/data/butler_bot.db"
            else:
                self.db_path = "butler_bot.db"
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    weather_notifications BOOLEAN DEFAULT 1,
                    weather_time TEXT DEFAULT '08:30',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица ежедневных задач
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_name TEXT NOT NULL,
                    time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица одноразовых задач
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS one_time_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_name TEXT NOT NULL,
                    scheduled_datetime TIMESTAMP NOT NULL,
                    is_completed BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица истории напоминаний (для отслеживания повторов)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminder_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_type TEXT, -- 'daily' или 'one_time'
                    task_id INTEGER,
                    reminder_time TIMESTAMP,
                    is_completed BOOLEAN DEFAULT 0,
                    next_reminder TIMESTAMP,
                    reminder_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            conn.commit()
            
            # Миграция: добавляем колонку weather_time если её нет
            self._migrate_database()
    
    def _migrate_database(self):
        """Выполняет миграции базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем наличие колонки weather_time
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'weather_time' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN weather_time TEXT DEFAULT '08:30'")
                print("✅ Миграция: добавлена колонка weather_time")
                conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавляет пользователя в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            """, (user_id, username, first_name))
            conn.commit()
    
    def get_user_weather_settings(self, user_id: int) -> Dict:
        """Получает настройки погоды пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT weather_notifications, weather_time
                FROM users
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'notifications_enabled': bool(result[0]),
                    'weather_time': result[1]
                }
            return {'notifications_enabled': True, 'weather_time': '08:30'}
    
    def update_user_weather_time(self, user_id: int, weather_time: str):
        """Обновляет время получения погоды для пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users
                SET weather_time = ?
                WHERE user_id = ?
            """, (weather_time, user_id))
            conn.commit()
    
    def toggle_weather_notifications(self, user_id: int) -> bool:
        """Переключает уведомления о погоде для пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Получаем текущее состояние
            cursor.execute("""
                SELECT weather_notifications FROM users WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            new_state = not bool(result[0]) if result else True
            
            cursor.execute("""
                UPDATE users
                SET weather_notifications = ?
                WHERE user_id = ?
            """, (new_state, user_id))
            conn.commit()
            return new_state
    
    def get_users_for_weather_time(self, time_str: str) -> List[Dict]:
        """Получает всех пользователей для определенного времени погоды"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, weather_time
                FROM users
                WHERE weather_notifications = 1 AND weather_time = ?
            """, (time_str,))
            
            rows = cursor.fetchall()
            return [
                {
                    'user_id': row[0],
                    'first_name': row[1],
                    'weather_time': row[2]
                }
                for row in rows
            ]
    
    def add_daily_task(self, user_id: int, task_name: str, time: str) -> int:
        """Добавляет ежедневную задачу"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_tasks (user_id, task_name, time)
                VALUES (?, ?, ?)
            """, (user_id, task_name, time))
            conn.commit()
            return cursor.lastrowid
    
    def add_one_time_task(self, user_id: int, task_name: str, scheduled_datetime: datetime.datetime) -> int:
        """Добавляет одноразовую задачу"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO one_time_tasks (user_id, task_name, scheduled_datetime)
                VALUES (?, ?, ?)
            """, (user_id, task_name, scheduled_datetime.isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_daily_tasks(self, user_id: int) -> List[Dict]:
        """Получает все активные ежедневные задачи пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task_name, time, created_at
                FROM daily_tasks
                WHERE user_id = ? AND is_active = 1
                ORDER BY time
            """, (user_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'task_name': row[1],
                    'time': row[2],
                    'created_at': row[3]
                }
                for row in rows
            ]
    
    def get_user_one_time_tasks(self, user_id: int) -> List[Dict]:
        """Получает все активные одноразовые задачи пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task_name, scheduled_datetime, created_at
                FROM one_time_tasks
                WHERE user_id = ? AND is_active = 1 AND is_completed = 0
                ORDER BY scheduled_datetime
            """, (user_id,))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'task_name': row[1],
                    'scheduled_datetime': row[2],
                    'created_at': row[3]
                }
                for row in rows
            ]
    
    def complete_one_time_task(self, task_id: int):
        """Отмечает одноразовую задачу как выполненную"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE one_time_tasks
                SET is_completed = 1
                WHERE id = ?
            """, (task_id,))
            conn.commit()
    
    def delete_daily_task(self, task_id: int):
        """Удаляет ежедневную задачу"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE daily_tasks
                SET is_active = 0
                WHERE id = ?
            """, (task_id,))
            conn.commit()
    
    def delete_one_time_task(self, task_id: int):
        """Удаляет одноразовую задачу"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE one_time_tasks
                SET is_active = 0
                WHERE id = ?
            """, (task_id,))
            conn.commit()
    
    def add_reminder_history(self, user_id: int, task_type: str, task_id: int, 
                           reminder_time: datetime.datetime, next_reminder: datetime.datetime = None):
        """Добавляет запись в историю напоминаний"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminder_history 
                (user_id, task_type, task_id, reminder_time, next_reminder, reminder_count)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (user_id, task_type, task_id, reminder_time.isoformat(), 
                  next_reminder.isoformat() if next_reminder else None))
            conn.commit()
            return cursor.lastrowid
    
    def update_reminder_history(self, reminder_id: int, next_reminder: datetime.datetime = None):
        """Обновляет историю напоминаний"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminder_history
                SET reminder_count = reminder_count + 1,
                    next_reminder = ?
                WHERE id = ?
            """, (next_reminder.isoformat() if next_reminder else None, reminder_id))
            conn.commit()
    
    def complete_reminder(self, reminder_id: int):
        """Отмечает напоминание как выполненное"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminder_history
                SET is_completed = 1, next_reminder = NULL
                WHERE id = ?
            """, (reminder_id,))
            conn.commit()
    
    def get_pending_reminders(self) -> List[Dict]:
        """Получает все активные напоминания, которые нужно отправить"""
        current_time = datetime.datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, task_type, task_id, next_reminder, reminder_count
                FROM reminder_history
                WHERE is_completed = 0 
                AND next_reminder IS NOT NULL 
                AND next_reminder <= ?
            """, (current_time.isoformat(),))
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'task_type': row[2],
                    'task_id': row[3],
                    'next_reminder': row[4],
                    'reminder_count': row[5]
                }
                for row in rows
            ]
    
    def get_tasks_for_time(self, target_time: str) -> List[Dict]:
        """Получает все ежедневные задачи для определенного времени"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT dt.id, dt.user_id, dt.task_name, dt.time, u.first_name
                FROM daily_tasks dt
                JOIN users u ON dt.user_id = u.user_id
                WHERE dt.time = ? AND dt.is_active = 1
            """, (target_time,))
            
            rows = cursor.fetchall()
            return [
                {
                    'task_id': row[0],
                    'user_id': row[1],
                    'task_name': row[2],
                    'time': row[3],
                    'first_name': row[4]
                }
                for row in rows
            ]
    
    def get_one_time_tasks_for_time(self, target_datetime: datetime.datetime) -> List[Dict]:
        """Получает все одноразовые задачи для определенного времени"""
        target_str = target_datetime.strftime("%Y-%m-%d %H:%M")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ott.id, ott.user_id, ott.task_name, ott.scheduled_datetime, u.first_name
                FROM one_time_tasks ott
                JOIN users u ON ott.user_id = u.user_id
                WHERE strftime('%Y-%m-%d %H:%M', ott.scheduled_datetime) = ? 
                AND ott.is_active = 1 AND ott.is_completed = 0
            """, (target_str,))
            
            rows = cursor.fetchall()
            return [
                {
                    'task_id': row[0],
                    'user_id': row[1],
                    'task_name': row[2],
                    'scheduled_datetime': row[3],
                    'first_name': row[4]
                }
                for row in rows
            ]
