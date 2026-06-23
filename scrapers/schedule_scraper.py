import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}

# Правильний формат URL: ?p=uk/schedule&s={faculty}-{group}
# Наприклад: fis-sp11, fmt-ma11, fem-bi11

def get_faculty_data(faculty_code: str) -> dict:
    """
    Повертає дані факультету:
    - groups_by_course: {курс: [(назва, код), ...]}
    - pdf_links: [(назва_файлу, url), ...]
    - exam_groups: [(назва групи, дата початку), ...]
    """
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException:
        return {"groups_by_course": {}, "pdf_links": [], "exam_groups": []}

    soup = BeautifulSoup(response.text, "html.parser")
    groups_by_course = {}
    pdf_links = []
    exam_groups = []

    # Збираємо PDF посилання для розкладу занять
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower() or ".PDF" in href:
            title = a.get_text(strip=True) or a.parent.get_text(strip=True)
            full_url = href if href.startswith("http") else TNTU_BASE_URL + href
            pdf_links.append((title[:80], full_url))

    # Збираємо групи з посиланнями на екзаменаційний розклад
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Формат посилань на групи: ?p=uk/schedule&s=fis-sp11
        if "?p=uk/schedule&s=" in href and "-" in href.split("&s=")[-1]:
            group_code = href.split("&s=")[-1]  # наприклад: fis-sp11
            group_name = a.get_text(strip=True)  # наприклад: СП-11

            if not group_name or len(group_name) > 15:
                continue

            # Витягуємо дату якщо є "(з ДД.ММ.РРРР)"
            parent_text = a.parent.get_text(strip=True) if a.parent else ""
            date_start = ""
            if "з " in parent_text:
                import re
                m = re.search(r"з (\d{2}\.\d{2}\.\d{4})", parent_text)
                if m:
                    date_start = m.group(1)

            exam_groups.append((group_name, group_code, date_start))

            # Групуємо по курсах
            digits = "".join(filter(str.isdigit, group_name))
            if len(digits) >= 2:
                course_num = digits[0]
                course_key = f"{course_num} курс"
                if course_key not in groups_by_course:
                    groups_by_course[course_key] = []
                entry = (group_name, group_code)
                if entry not in groups_by_course[course_key]:
                    groups_by_course[course_key].append(entry)

    return {
        "groups_by_course": dict(sorted(groups_by_course.items())),
        "pdf_links": pdf_links[:10],
        "exam_groups": exam_groups,
    }


def get_exam_schedule(group_code: str) -> str:
    """
    Парсить і повертає розклад екзаменів для конкретної групи.
    group_code — повний код, наприклад: fis-sp11
    """
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={group_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException:
        return f"❌ Не вдалося завантажити розклад. Спробуй пізніше.\n\n🔗 {url}"

    soup = BeautifulSoup(response.text, "html.parser")

    # Витягуємо основний контент — шукаємо таблиці і списки з іспитами
    lines = []
    group_name = group_code.split("-")[-1].upper()

    # Шукаємо заголовок групи
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if any(c.isupper() for c in text) and len(text) < 30 and ("група" in text.lower() or any(d.isdigit() for d in text)):
            group_name = text
            break

    # Шукаємо всі текстові блоки з датами та предметами
    content_blocks = []
    in_schedule = False

    for tag in soup.find_all(["h2", "h3", "h4", "p", "li", "div"]):
        text = tag.get_text(separator=" ", strip=True)

        if not text or len(text) < 3:
            continue

        # Починаємо збирати після заголовка з назвою групи або "розклад"
        if tag.name in ("h2", "h3") and (
            "розклад" in text.lower() or
            "екзамен" in text.lower() or
            any(c.isupper() for c in text[:5])
        ):
            in_schedule = True

        if not in_schedule:
            continue

        # Зупиняємось на футері
        if "права" in text.lower() or "©" in text or len(text) > 500:
            continue

        # Дати — містять місяць
        months = ["січня", "лютого", "березня", "квітня", "травня", "червня",
                  "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
        has_date = any(m in text.lower() for m in months)

        # Час — містить двокрапку між цифрами
        has_time = any(f":{d}" in text for d in "0123456789")

        # Предмет — є посилання або довгий текст
        has_link = bool(tag.find("a"))

        if has_date or has_time or (has_link and len(text) > 10):
            content_blocks.append(text)

    # Якщо нічого не знайшли — витягуємо весь текст контентної зони
    if not content_blocks:
        main_div = soup.find("div", {"id": "content"}) or soup.find("main") or soup.find("article")
        if main_div:
            raw = main_div.get_text(separator="\n", strip=True)
            # Беремо лише рядки з датами/часом
            for line in raw.split("\n"):
                line = line.strip()
                if len(line) > 5 and (
                    any(m in line.lower() for m in months) or
                    ":" in line or
                    "ауд" in line.lower()
                ):
                    content_blocks.append(line)

    if not content_blocks:
        return (
            f"📋 Розклад екзаменів — група {group_name.upper()}\n\n"
            "Детальний розклад ще не опубліковано або відображається у спеціальному форматі.\n\n"
            f"🔗 Переглянь на сайті ТНТУ:\n{url}"
        )

    # Форматуємо результат
    result = [f"📝 Розклад екзаменів — {group_name.upper()}\n"]
    seen = set()
    for block in content_blocks[:20]:
        if block not in seen and len(block) > 3:
            seen.add(block)
            result.append(block)

    result.append(f"\n🔗 Повний розклад на сайті ТНТУ:\n{url}")
    return "\n".join(result)


def get_schedule_pdfs(faculty_code: str, group_name: str) -> str:
    """
    Повертає PDF посилання на розклад занять для групи.
    """
    data = get_faculty_data(faculty_code)
    pdfs = data.get("pdf_links", [])

    group_upper = group_name.upper()
    # Шукаємо PDF де згадується група
    relevant = [(t, u) for t, u in pdfs if group_upper.split("-")[0] in t.upper()]

    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"

    if not pdfs:
        return (
            f"📅 Розклад занять — група {group_upper}\n\n"
            "PDF з розкладом ще не завантажено або розклад доступний лише на сайті.\n\n"
            f"🔗 Перейди на сторінку факультету:\n{url}"
        )

    lines = [f"📅 Розклад занять — група {group_upper}\n"]
    lines.append("Оберіть потрібний PDF файл:\n")

    target_pdfs = relevant if relevant else pdfs[:5]
    for title, pdf_url in target_pdfs:
        lines.append(f"📄 {title}\n{pdf_url}\n")

    lines.append(f"🔗 Всі розклади:\n{url}")
    return "\n".join(lines)