import time
import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}
_cache: dict = {"data": [], "ts": 0}
CACHE_TTL = 1800  # 30 хв


def get_news(limit: int = 7) -> list[dict]:
    global _cache
    if _cache["data"] and (time.time() - _cache["ts"]) < CACHE_TTL:
        return _cache["data"][:limit]

    try:
        r = requests.get(f"{TNTU_BASE_URL}/?p=uk/main", headers=HEADERS, timeout=8)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return _cache["data"][:limit]

    items, in_news = [], False
    for tag in soup.find_all(["h2","h3","li"]):
        text = tag.get_text(strip=True)
        if tag.name in ("h2","h3") and "Новини" in text:
            in_news = True; continue
        if in_news and tag.name in ("h2","h3") and "Новини" not in text:
            break
        if in_news and tag.name == "li":
            a = tag.find("a", href=True)
            if a and "/news/" in a.get("href",""):
                href = a["href"]
                full = href if href.startswith("http") else f"{TNTU_BASE_URL}{href}"
                title = tag.get_text(separator=" ", strip=True)
                items.append({"title": title, "url": full})
            if len(items) >= 10:
                break

    if items:
        _cache = {"data": items, "ts": time.time()}
    return items[:limit]


def format_news(items: list[dict]) -> str:
    if not items:
        return "❌ Не вдалося завантажити новини. Спробуй пізніше."
    lines = ["📰 <b>Останні новини ТНТУ</b>\n"]
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. <a href=\"{it['url']}\">{it['title']}</a>")
    lines.append(f"\n🔗 <a href=\"{TNTU_BASE_URL}/?p=uk/news\">Всі новини ТНТУ</a>")
    return "\n".join(lines)