"""
Модуль для работы с погодой

Обеспечивает получение данных о погоде через WeatherAPI
и генерирует умные рекомендации по одежде на основе:
- Температуры воздуха и ощущаемой температуры
- Скорости и направления ветра  
- Погодных условий и осадков
- Влажности воздуха

Координаты: Нижний Новгород (56.313398, 44.051441)
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Константы
NIZHNY_NOVGOROD_COORDS = "56.313398,44.051441"
API_BASE_URL = "https://api.weatherapi.com/v1/forecast.json"

# Пороги температуры для рекомендаций одежды
TEMP_THRESHOLDS = {
    'HOT': 25,
    'WARM': 18,
    'MILD': 15,
    'COOL': 10,
    'COLD': 5,
    'VERY_COLD': -5
}

# Пороги скорости ветра
WIND_THRESHOLDS = {
    'STRONG': 20,
    'MODERATE': 10
}

class WeatherService:
    def __init__(self):
        self.api_key = os.environ.get('WEATHER_API_TOKEN')
        self.base_url = API_BASE_URL
        self.location = NIZHNY_NOVGOROD_COORDS
    
    def get_weather_data(self):
        """Получает данные о погоде"""
        try:
            params = {
                'key': self.api_key,
                'q': self.location,
                'lang': 'ru',
                'days': 1
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения погоды: {e}")
            return None
    
    def get_clothing_recommendation(self, temp_c, feels_like_c, wind_kph, condition):
        """Рекомендует одежду в зависимости от погоды"""
        clothing = []
        
        # Базовая одежда по температуре ощущения
        if feels_like_c >= TEMP_THRESHOLDS['HOT']:
            clothing.append("👕 футболка")
        elif feels_like_c >= TEMP_THRESHOLDS['WARM']:
            clothing.append("👕 футболка и легкая рубашка")
        elif feels_like_c >= TEMP_THRESHOLDS['MILD']:
            clothing.append("👔 легкая кофта")
        elif feels_like_c >= TEMP_THRESHOLDS['COOL']:
            clothing.append("🧥 тёплая толстовка или свитер")
        elif feels_like_c >= TEMP_THRESHOLDS['COLD']:
            clothing.append("🧥 весенняя куртка")
        elif feels_like_c >= TEMP_THRESHOLDS['VERY_COLD']:
            clothing.append("🧥 демисезонная куртка")
        else:
            clothing.append("🧥 зимняя куртка")
        
        # Дополнительные рекомендации по ветру
        if wind_kph > WIND_THRESHOLDS['STRONG']:
            clothing.append("🌪️ что-то от ветра (сильный ветер)")
        elif wind_kph > WIND_THRESHOLDS['MODERATE']:
            clothing.append("🌪️ легкая защита от ветра")
        
        # Рекомендации по осадкам
        condition_lower = condition.lower()
        rain_keywords = ['дождь', 'ливень', 'морось', 'дождливо']
        snow_keywords = ['снег', 'метель', 'вьюга', 'снежно']
        
        if any(word in condition_lower for word in rain_keywords):
            clothing.append("☂️ зонт или дождевик")
        elif any(word in condition_lower for word in snow_keywords):
            clothing.append("❄️ теплая зимняя одежда с капюшоном")
        
        return clothing
    
    def format_weather_message(self):
        """Форматирует сообщение о погоде"""
        weather_data = self.get_weather_data()
        
        if not weather_data:
            return "❌ Не удалось получить данные о погоде"
        
        try:
            current = weather_data['current']
            location = weather_data['location']
            
            temp_c = current['temp_c']
            feels_like_c = current['feelslike_c']
            condition = current['condition']['text']
            wind_kph = current['wind_kph']
            wind_dir = current['wind_dir']
            
            # Получаем рекомендации по одежде
            clothing = self.get_clothing_recommendation(temp_c, feels_like_c, wind_kph, condition)
            
            message = f"""🌤️ *Погода в {location['name']}*

🌡️ *Температура:* {temp_c}°C (ощущается как {feels_like_c}°C)
☁️ *Погода:* {condition}
💨 *Ветер:* {wind_kph} км/ч, {wind_dir}

👔 *Рекомендации по одежде:*
{chr(10).join([f"• {item}" for item in clothing])}
"""
            
            return message
            
        except KeyError as e:
            return f"❌ Ошибка обработки данных погоды: {e}"
