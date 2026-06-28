"""
Курс валют з https://rulya-bank.com.ua/
Формат рядка: USD USD 44.50 +0.10 10.06 45.30 -0.10 11.06
"""
import re
import time
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup

URL     = "https://rulya-bank.com.ua/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

_cache: dict = {"data": [], "ts": 0.0, "label": ""}

CURRENCIES = ["USD", "EUR", "GBP", "CHF", "CAD", "PLZ"]

FLAGS = {
    "USD":"🇺🇸","EUR":"🇪🇺","GBP":"🇬🇧",
    "CHF":"🇨🇭","CAD":"🇨🇦","PLZ":"🇵🇱","PLN":"🇵🇱",
}
NAMES = {
    "USD":"Долар США","EUR":"Євро","GBP":"Фунт стерлінгів",
    "CHF":"Швейцарський франк","CAD":"Канадський долар",
    "PLZ":"Польський злотий","PLN":"Польський злотий",
}


def _next_8am() -> float:
    import datetime as dt
    now = datetime.now()
    t8  = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now.hour >= 8:
        t8 += dt.timedelta(days=1)
    return t8.timestamp()


def _parse_row(parts: list[str]) -> dict | None:
    """
    Парсить список слів одного рядку валюти.
    Формат: [USD, USD, 44.50, +0.10, 10.06, 45.30, -0.10, 11.06]
    або     [USD, 44.50, +0.10, 10.06, 45.30, -0.10, 11.06]
    """
    if not parts:
        return None
    code = parts[0].upper()
    if code not in CURRENCIES:
        return None
    # Пропускаємо якщо код повторюється двічі
    rest = parts[1:] if (len(parts) > 1 and parts[1].upper() == code) else parts[1:]
    # Шукаємо числа і зміни
    nums    = []
    changes = []
    for p in rest:
        if re.match(r'^\d+\.\d+$', p):
            nums.append(float(p))
        elif re.match(r'^[+\-]\d+\.\d+$', p):
            changes.append(p)
    if len(nums) < 2:
        return None
    return {
        "code":   code,
        "name":   NAMES.get(code, code),
        "buy":    nums[0],
        "sell":   nums[1],
        "chg_b":  changes[0] if len(changes) > 0 else "",
        "chg_s":  changes[1] if len(changes) > 1 else "",
    }


def _scrape() -> tuple[list[dict], str]:
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return [], ""

    # Мітка часу: "Курс валют станом на [**8:00**] 27.06.2026"
    label = ""
    text  = soup.get_text()
    m = re.search(r"станом на\s*\[?\*?\*?(\d{1,2}:\d{2})\*?\*?\]?\s*([\d.]+)", text)
    if m:
        label = f"{m.group(1)}, {m.group(2)}"

    results = []
    for li in soup.find_all("li"):
        raw   = li.get_text(separator=" ", strip=True)
        parts = raw.split()
        row   = _parse_row(parts)
        if row:
            results.append(row)

    return results, label


def _get() -> tuple[list[dict], str]:
    global _cache
    now = time.time()
    if _cache["data"] and now < _cache["ts"]:
        return _cache["data"], _cache["label"]
    data, label = _scrape()
    if data:
        _cache = {"data": data, "ts": _next_8am(), "label": label}
    return (_cache["data"], _cache["label"]) if _cache["data"] else ([], label)


def get_currency() -> str:
    data, label = _get()
    if not data:
        return (f"❌ Не вдалося отримати курс валют.\n\n"
                f"🔗 <a href=\"{URL}\">rulya-bank.com.ua</a>")

    today = date.today().strftime("%d.%m.%Y")
    when  = f"<b>{label}</b>" if label else f"<b>8:00, {today}</b>"

    lines = [
        f"💱 <b>Курс валют</b> — станом на {when}",
        f"🏦 <a href=\"{URL}\">Рульовий банк, Тернопіль</a>",
        "",
        f"<code>{'Валюта':<8} {'Купівля':>8}  {'Продаж':>8}</code>",
        f"<code>{'─'*30}</code>",
    ]

    for d in data:
        flag = FLAGS.get(d["code"], "")
        buy  = f"{d['buy']:.2f}"
        sell = f"{d['sell']:.2f}"
        cb   = d["chg_b"] if d["chg_b"] else "      "
        cs   = d["chg_s"] if d["chg_s"] else "      "
        lines.append(
            f"{flag} <code>{d['code']:<5} {buy:>7} {cb:<7}  {sell:>7} {cs:<7}</code>"
        )

    lines.append(f"<code>{'─'*30}</code>")
    lines.append(f"<i>Оновлення щодня о 8:00</i>")
    return "\n".join(lines)


def get_currency_detail(code: str) -> str:
    data, label = _get()
    d = next((x for x in data if x["code"] == code.upper()), None)
    if not d:
        return f"❌ Валюту <b>{code}</b> не знайдено."
    flag = FLAGS.get(d["code"], "")
    return (
        f"{flag} <b>{d['name']} ({d['code']})</b>\n"
        f"{'─'*24}\n"
        f"📈 Купівля:  <b>{d['buy']:.2f} грн</b>"
        + (f"  <i>{d['chg_b']}</i>" if d["chg_b"] else "") + "\n"
        f"📉 Продаж:   <b>{d['sell']:.2f} грн</b>"
        + (f"  <i>{d['chg_s']}</i>" if d["chg_s"] else "") + "\n\n"
        f"🔗 <a href=\"{URL}\">rulya-bank.com.ua</a>"
    )