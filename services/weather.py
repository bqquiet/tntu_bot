import requests
from config import WEATHER_API_KEY, WEATHER_CITY


# Таблиця погодних умов → емодзі
WEATHER_EMOJI = {
    "clear sky": "☀️",
    "few clouds": "🌤",
    "scattered clouds": "⛅️",
    "broken clouds": "☁️",
    "overcast clouds": "☁️",
    "light rain": "🌦",
    "moderate rain": "🌧",
    "heavy intensity rain": "🌧",
    "thunderstorm": "⛈",
    "snow": "❄️",
    "light snow": "🌨",
    "mist": "🌫",
    "fog": "🌫",
    "drizzle": "🌦",
}

WIND_DIRECTIONS = [
    "Пн", "ПнСх", "Сх", "ПдСх",
    "Пд", "ПдЗх", "Зх", "ПнЗх", "Пн"
]


def get_weather() -> str:
    """
    Отримує поточну погоду в Тернополі через OpenWeatherMap API.
    Безкоштовний план — до 1000 запитів/день.
    """
    if WEATHER_API_KEY == "ВСТАВ_СВІЙ_КЛЮЧ_ТУТ":
        return (
            "⚙️ API-ключ для погоди не налаштований\\.\n"
            "Зареєструйся на openweathermap\\.org і встав ключ у config\\.py"
        )

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": WEATHER_CITY,
        "appid": WEATHER_API_KEY,
        "lang": "uk",
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception:
        return "❌ Не вдалося отримати погоду\\. Спробуй пізніше\\."

    if data.get("cod") != 200:
        return f"❌ Помилка API погоди: {data.get('message', 'невідома помилка')}"

    # Основні дані
    temp = round(data["main"]["temp"])
    feels = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    description = data["weather"][0]["description"].capitalize()
    desc_en = data["weather"][0]["main"].lower()
    wind_speed = data["wind"]["speed"]
    wind_deg = data["wind"].get("deg", 0)

    # Емодзі погоди
    emoji = WEATHER_EMOJI.get(data["weather"][0]["description"].lower(), "🌡")

    # Напрям вітру
    wind_dir = WIND_DIRECTIONS[round(wind_deg / 45) % 8]

    # Порада
    tip = _get_tip(data)

    lines = [
        f"{emoji} *Погода в Тернополі*\n",
        f"🌡 Температура: *{temp}°C* (відчувається як {feels}°C)",
        f"☁️ {description}",
        f"💧 Вологість: {humidity}%",
        f"💨 Вітер: {wind_speed} м/с, {wind_dir}",
    ]

    if tip:
        lines.append(f"\n💡 {tip}")

    return "\n".join(lines)


def _get_tip(data: dict) -> str:
    """Порада для студента на основі погоди."""
    desc = data["weather"][0]["description"].lower()
    temp = data["main"]["temp"]

    if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
        return "Візьми парасольку! ☂️"
    if temp < 0:
        return "Одягнись тепліше! 🧥"
    if temp < 5:
        return "Холодно — не забудь куртку! 🧤"
    if temp > 28:
        return "Спекотно — візьми воду! 💧"
    if "snow" in desc:
        return "На вулиці сніг — обережно на слизькому! ❄️"
    return ""
