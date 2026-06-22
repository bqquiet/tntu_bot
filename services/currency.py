import requests
from datetime import date


def get_currency() -> str:
    """
    Отримує курс валют від НБУ.
    API не потребує реєстрації чи ключів — повністю безкоштовне.
    """
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception:
        return "❌ Не вдалося отримати курс валют. Спробуй пізніше."

    # Шукаємо потрібні валюти
    currencies = {item["cc"]: item for item in data}
    today = date.today().strftime("%d.%m.%Y")

    lines = [f"💱 *Курс валют НБУ на {today}*\n"]

    if "USD" in currencies:
        rate = currencies["USD"]["rate"]
        lines.append(f"🇺🇸 USD (долар):  *{rate:.2f} грн*")

    if "EUR" in currencies:
        rate = currencies["EUR"]["rate"]
        lines.append(f"🇪🇺 EUR (євро):   *{rate:.2f} грн*")

    if "GBP" in currencies:
        rate = currencies["GBP"]["rate"]
        lines.append(f"🇬🇧 GBP (фунт):   *{rate:.2f} грн*")

    if "PLN" in currencies:
        rate = currencies["PLN"]["rate"]
        lines.append(f"🇵🇱 PLN (злотий): *{rate:.2f} грн*")

    lines.append("\n_Офіційний курс Національного банку України_")
    return "\n".join(lines)
