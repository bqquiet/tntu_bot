import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}


def get_news(limit: int = 6) -> list[dict]:
    """
    Повертає список останніх новин ТНТУ.
    Кожна новина: {"title": str, "url": str}
    """
    url = f"{TNTU_BASE_URL}/?p=uk/main"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []

    # Знаходимо заголовок "Новини" і беремо <li> після нього
    in_news = False
    for tag in soup.find_all(["h3", "li"]):
        if tag.name == "h3" and "Новини" in tag.text:
            in_news = True
            continue

        if in_news and tag.name == "h3":
            break  # наступна секція — зупиняємось

        if in_news and tag.name == "li":
            a = tag.find("a", href=True)
            if a and "/news/" in a["href"]:
                # Збираємо повний текст новини (включно з <strong>)
                title = tag.get_text(separator=" ", strip=True)
                href = a["href"]
                if not href.startswith("http"):
                    href = TNTU_BASE_URL + href
                news_items.append({"title": title, "url": href})

            if len(news_items) >= limit:
                break

    return news_items


def format_news(news_items: list[dict]) -> str:
    if not news_items:
        return "❌ Не вдалося завантажити новини. Спробуй пізніше."

    lines = ["📰 *Останні новини ТНТУ*\n"]
    for i, item in enumerate(news_items, 1):
        lines.append(f"{i}\\. [{item['title']}]({item['url']})")

    lines.append(f"\n🔗 [Всі новини]({TNTU_BASE_URL}/?p=uk/news)")
    return "\n".join(lines)
