import time
import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}

# Простий кеш — зберігаємо результат на 30 хвилин
_cache: dict = {"data": [], "ts": 0}
CACHE_TTL = 30 * 60  # 30 хвилин


def get_news(limit: int = 7) -> list[dict]:
    global _cache
    if _cache["data"] and (time.time() - _cache["ts"]) < CACHE_TTL:
        return _cache["data"][:limit]

    url = f"{TNTU_BASE_URL}/?p=uk/main"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = "utf-8"
    except requests.RequestException:
        return _cache["data"][:limit] if _cache["data"] else []

    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    in_news = False

    for tag in soup.find_all(["h3", "h2", "li", "a"]):
        text = tag.get_text(strip=True)

        if tag.name in ("h2", "h3") and "Новини" in text:
            in_news = True
            continue

        if in_news and tag.name in ("h2", "h3") and "Новини" not in text:
            break

        if in_news and tag.name == "li":
            a = tag.find("a", href=True)
            if a and "/news/" in a.get("href", ""):
                title = tag.get_text(separator=" ", strip=True)
                href = a["href"]
                full = href if href.startswith("http") else f"{TNTU_BASE_URL}{href}"
                items.append({"title": title, "url": full})
            if len(items) >= 10:
                break

    if items:
        _cache = {"data": items, "ts": time.time()}

    return items[:limit]


def format_news(items: list[dict]) -> str:
    if not items:
        return "❌ Не вдалося завантажити новини. Спробуй пізніше."

    lines = ["📰 Останні новини ТНТУ\n"]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item['title']}\n{item['url']}\n")
    lines.append(f"🔗 Всі новини: {TNTU_BASE_URL}/?p=uk/news")
    return "\n".join(lines)