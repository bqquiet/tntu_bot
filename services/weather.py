import requests
from config import WEATHER_API_KEY, WEATHER_CITY

EMOJI = {
    "clear sky":"☀️","few clouds":"🌤","scattered clouds":"⛅️",
    "broken clouds":"☁️","overcast clouds":"☁️","light rain":"🌦",
    "moderate rain":"🌧","heavy intensity rain":"🌧","thunderstorm":"⛈",
    "snow":"❄️","light snow":"🌨","mist":"🌫","fog":"🌫","drizzle":"🌦",
}
DIRS = ["Пн","ПнСх","Сх","ПдСх","Пд","ПдЗх","Зх","ПнЗх"]


def get_weather() -> str:
    if not WEATHER_API_KEY:
        return ("⚙️ <b>API ключ не налаштований</b>\n\n"
                "Зареєструйся на <a href=\"https://openweathermap.org\">openweathermap.org</a> "
                "і додай ключ у файл .env")

    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": WEATHER_CITY, "appid": WEATHER_API_KEY,
                    "lang": "uk", "units": "metric"},
            timeout=8
        )
        d = r.json()
    except Exception:
        return "❌ Не вдалося отримати погоду. Спробуй пізніше."

    if d.get("cod") != 200:
        return f"❌ Помилка: {d.get('message','невідома')}"

    temp   = round(d["main"]["temp"])
    feels  = round(d["main"]["feels_like"])
    hum    = d["main"]["humidity"]
    desc   = d["weather"][0]["description"].capitalize()
    desc_e = d["weather"][0]["description"].lower()
    wind   = d["wind"]["speed"]
    deg    = d["wind"].get("deg", 0)
    emoji  = EMOJI.get(desc_e, "🌡")
    wdir   = DIRS[round(deg / 45) % 8]

    tip = ""
    if any(w in desc_e for w in ["rain","drizzle","thunderstorm"]):
        tip = "\n☂️ <i>Візьми парасольку!</i>"
    elif temp < 0:
        tip = "\n🧥 <i>Одягнись тепліше!</i>"
    elif temp < 5:
        tip = "\n🧤 <i>Не забудь куртку!</i>"
    elif temp > 28:
        tip = "\n💧 <i>Спекотно — візьми воду!</i>"

    return (
        f"{emoji} <b>Погода в Тернополі</b>\n"
        f"{'─'*24}\n"
        f"🌡 Температура: <b>{temp}°C</b> (відчувається {feels}°C)\n"
        f"☁️ {desc}\n"
        f"💧 Вологість: {hum}%\n"
        f"💨 Вітер: {wind} м/с, {wdir}{tip}"
    )