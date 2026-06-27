"""
Курс валют з https://rulya-bank.com.ua/
Оновлюється щодня о 8:00 — кеш тримаємо до наступного оновлення.
"""
import re
import time
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup

URL     = "https://rulya-bank.com.ua/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Кеш: {data: [...], ts: float, update_label: str}
_cache: dict = {"data": [], "ts": 0.0, "update_label": ""}

# Валюти котрі показуємо в боті (в порядку відображення)
TARGET = ["USD", "EUR", "GBP", "CHF", "CAD", "PLZ", "PLN"]

FLAGS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧",
    "CHF": "🇨🇭", "CAD": "🇨🇦", "PLZ": "🇵🇱", "PLN": "🇵🇱",
}

NAMES = {
    "USD": "Долар США",    "EUR": "Євро",
    "GBP": "Фунт стерлінгів", "CHF": "Швейцарський франк",
    "CAD": "Канадський долар","PLZ": "Польський злотий",
    "PLN": "Польський злотий",
}


def _next_8am() -> float:
    """Повертає unix-час наступного оновлення (8:00 сьогодні або завтра)."""
    now = datetime.now()
    today_8 = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now.hour >= 8:
        import datetime as dt
        today_8 += dt.timedelta(days=1)
    return today_8.timestamp()


def _scrape() -> tuple[list[dict], str]:
    """
    Парсить сайт і повертає (список валют, мітку часу оновлення).
    Кожен елемент: {code, name, buy, sell, change_buy, change_sell}
    """
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        return [], ""

    # ── Мітка часу оновлення ─────────────────────────────────────────────────
    update_label = ""
    body_text = soup.get_text()
    m = re.search(r"станом на\s*\[?\*?\*?(\d{1,2}:\d{2})\*?\*?\]?\s*([\d.]+)", body_text)
    if m:
        update_label = f"{m.group(1)}, {m.group(2)}"

    # ── Парсимо таблицю курсів ────────────────────────────────────────────────
    results = []

    # Шукаємо <ul> з курсами або <li> рядки
    items = soup.find_all("li")
    for li in items:
        text = li.get_text(separator=" ", strip=True)
        # Пропускаємо заголовок
        if "Валюта" in text and "Купівля" in text:
            continue
        # Пропускаємо крос-курси (EUR/USD тощо)
        if "/" in text.split()[0] if text else True:
            continue

        # Очікуваний формат: "USD USD 44.50 +0.10 10.06 45.30 -0.10 11.06"
        # або                "USD 44.50 +0.10 10.06 45.30 -0.10 11.06"
        parts = text.split()
        if len(parts) < 4:
            continue

        # Перше слово — код валюти
        code = parts[0].upper()
        if code not in TARGET and code not in ["USD","EUR","GBP","CHF","CAD","PLZ","PLN"]:
            continue

        # Якщо є дублювання коду (USD USD ...) — пропускаємо перше
        offset = 1 if (len(parts) > 1 and parts[1].upper() == code) else 0
        rest = parts[1 + offset:]

        # Числа: перше — купівля, потім зміна (+/-), потім дата, потім продаж...
        nums = []
        changes = []
        i = 0
        while i < len(rest):
            p = rest[i]
            # Число з крапкою — курс
            if re.match(r'^\d+\.\d+$', p):
                nums.append(float(p))
            # Зміна
            elif re.match(r'^[+\-]\d+\.\d+$', p):
                changes.append(p)
            i += 1

        if len(nums) < 2:
            continue

        buy  = nums[0]
        sell = nums[1]
        cb   = changes[0] if len(changes) > 0 else ""
        cs   = changes[1] if len(changes) > 1 else ""

        results.append({
            "code":         code,
            "name":         NAMES.get(code, code),
            "buy":          buy,
            "sell":         sell,
            "change_buy":   cb,
            "change_sell":  cs,
        })

    return results, update_label


def _get_data() -> tuple[list[dict], str]:
    """Повертає дані з кешу або парсить свіжі."""
    global _cache
    now = time.time()

    # Кеш дійсний до наступних 8:00
    if _cache["data"] and now < _cache["ts"]:
        return _cache["data"], _cache["update_label"]

    data, label = _scrape()
    if data:
        _cache = {"data": data, "ts": _next_8am(), "update_label": label}
    elif _cache["data"]:
        return _cache["data"], _cache["update_label"]  # стара копія

    return data, label


def get_currency() -> str:
    data, label = _get_data()

    if not data:
        return (
            "❌ Не вдалося отримати курс валют.\n\n"
            f"🔗 <a href=\"{URL}\">rulya-bank.com.ua</a>"
        )

    today = date.today().strftime("%d.%m.%Y")
    update_str = f"станом на <b>{label}</b>" if label else f"<b>{today}</b>"

    lines = [
        f"💱 <b>Курс валют</b> — {update_str}",
        f"🏦 <a href=\"{URL}\">Рульовий банк, Тернопіль</a>",
        f"{'─' * 30}",
        f"{'Валюта':<6}  {'Купівля':>8}  {'Продаж':>8}",
        f"{'─' * 30}",
    ]

    for item in data:
        flag  = FLAGS.get(item["code"], "🏳")
        code  = item["code"]
        buy   = f"{item['buy']:.2f}"
        sell  = f"{item['sell']:.2f}"
        cb    = f" <i>{item['change_buy']}</i>"  if item["change_buy"]  else ""
        cs    = f" <i>{item['change_sell']}</i>" if item["change_sell"] else ""

        lines.append(
            f"{flag} <b>{code}</b>  "
            f"<code>{buy:>7}</code>{cb}  "
            f"<code>{sell:>7}</code>{cs}"
        )

    lines.append(f"{'─' * 30}")
    lines.append(f"<i>Оновлення щодня о 8:00</i>")
    return "\n".join(lines)


def get_currency_detail(code: str) -> str:
    """Детальна картка однієї валюти."""
    data, label = _get_data()
    item = next((x for x in data if x["code"] == code.upper()), None)
    if not item:
        return f"❌ Валюту <b>{code}</b> не знайдено."

    flag = FLAGS.get(item["code"], "🏳")
    cb   = f"  {item['change_buy']}"  if item["change_buy"]  else ""
    cs   = f"  {item['change_sell']}" if item["change_sell"] else ""

    return (
        f"{flag} <b>{item['name']} ({item['code']})</b>\n"
        f"{'─' * 24}\n"
        f"📈 Купівля: <b>{item['buy']:.2f} грн</b>{cb}\n"
        f"📉 Продаж:  <b>{item['sell']:.2f} грн</b>{cs}\n\n"
        f"🏦 <a href=\"{URL}\">rulya-bank.com.ua</a>"
    )