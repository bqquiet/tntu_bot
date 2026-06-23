from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN        = os.getenv("BOT_TOKEN", "")
WEATHER_API_KEY  = os.getenv("WEATHER_API_KEY", "")
WEATHER_CITY     = "Ternopil,UA"
TNTU_BASE_URL    = "https://tntu.edu.ua"

FACULTIES = {
    "ФМТ": "fmt",
    "ФПТ": "fpt",
    "ФІС": "fis",
    "ФЕМ": "fem",
}

COURSES = ["1 курс", "2 курс", "3 курс", "4 курс"]