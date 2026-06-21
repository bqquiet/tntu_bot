import os

# Токен бота від @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "8868564617:AAFC_JntIUuwP9T6YSCLYIyURKBpiEadoxc")

# API ключ від openweathermap.org (безкоштовна реєстрація)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "2d8f7e902b2da4fdc9dd8355dcbd2fd8")

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
