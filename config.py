import os

# Токен бота від @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВ_СВІЙ_ТОКЕН_ТУТ")

# API ключ від openweathermap.org (безкоштовна реєстрація)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "ВСТАВ_СВІЙ_КЛЮЧ_ТУТ")

# Місто для погоди
WEATHER_CITY = "Ternopil,UA"

# URL сайту ТНТУ
TNTU_BASE_URL = "https://tntu.edu.ua"
TNTU_SCHEDULE_URL = f"{TNTU_BASE_URL}/?p=uk/schedule"

# Факультети
FACULTIES = {
    "ФМТ": "fmt",
    "ФПТ": "fpt",
    "ФІС": "fis",
    "ФЕМ": "fem",
}

# Курси
COURSES = ["1 курс", "2 курс", "3 курс", "4 курс"]
