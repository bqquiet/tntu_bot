import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}


def get_faculty_data(faculty_code: str) -> dict:
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
    except requests.RequestException:
        return {"groups_by_course": {}, "pdf_links": []}

    soup = BeautifulSoup(r.text, "html.parser")
    groups_by_course = {}
    pdf_links = []

    # ── PDF посилання на розклади занять ──────────────────────────────────
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            title = a.get_text(strip=True) or "Розклад"
            # Правильне склеювання URL
            full_url = href if href.startswith("http") else urljoin(TNTU_BASE_URL + "/", href)
            if title and full_url not in [u for _, u in pdf_links]:
                pdf_links.append((title[:100], full_url))

    # ── Групи з посиланнями на екзаменаційний розклад ────────────────────
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "?p=uk/schedule&s=" not in href:
            continue
        code_part = href.split("&s=")[-1]
        # Пропускаємо факультетні посилання (fmt, fpt, fis, fem)
        if code_part in ("fmt", "fpt", "fis", "fem", faculty_code):
            continue
        # Групові посилання містять цифри
        if not any(c.isdigit() for c in code_part):
            continue

        group_name = a.get_text(strip=True).split("(")[0].strip()
        if not group_name or len(group_name) > 15:
            continue

        # Нормалізуємо код групи
        group_code = code_part  # напр. fis-sp11 або sp11

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
        "pdf_links": pdf_links[:15],
    }


def get_exam_schedule(group_code: str, group_name: str = "") -> str:
    """Парсить розклад екзаменів групи."""
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={group_code}"
    display_name = group_name or group_code.split("-")[-1].upper()

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
    except requests.RequestException:
        return f"❌ Не вдалося завантажити розклад.\n\n🔗 {url}"

    soup = BeautifulSoup(r.text, "html.parser")

    # Знаходимо основний контент — шукаємо блок після навігації
    # Пропускаємо nav, header, sidebar
    for tag in soup.find_all(["nav", "header", "aside"]):
        tag.decompose()

    months = ["січня","лютого","березня","квітня","травня","червня",
              "липня","серпня","вересня","жовтня","листопада","грудня"]

    # Шукаємо блоки з датами іспитів
    exam_entries = []
    current_date = ""

    content = soup.find("main") or soup.find("div", {"id": "content"}) or \
              soup.find("div", {"class": ["content","main-content","entry-content"]}) or soup

    for tag in content.find_all(["h2","h3","h4","p","li","div","td"]):
        text = " ".join(tag.get_text().split()).strip()

        if not text or len(text) > 400 or len(text) < 3:
            continue

        # Пропускаємо якщо схоже на навігацію
        nav_words = ["факультет","студенту","головна","меню","copyright","пошук","новини"]
        if any(w in text.lower() for w in nav_words):
            continue

        # Знаходимо дату
        words = text.split()
        if len(words) == 2 and words[0].isdigit() and any(m in words[1].lower() for m in months):
            current_date = text
            continue

        # Довша дата типу "19 червня 2026"
        if len(words) == 3 and words[0].isdigit() and any(m in words[1].lower() for m in months) and words[2].isdigit():
            current_date = text
            continue

        # Знаходимо предмет (є посилання або достатньо довгий)
        has_link = bool(tag.find("a"))
        has_time = bool(next((w for w in words if ":" in w and w.replace(":","").isdigit()), None))
        is_room  = bool(next((w for w in words if w.upper().startswith(("К","ЛАБ","АУД"))), None))

        if current_date and (has_link or has_time or is_room or len(text) > 20):
            # Час
            time_str = next((w for w in words if ":" in w and len(w) == 5), "")
            # Аудиторія
            room_str = next((w for w in words if w.upper().startswith(("К1","К2","К3","К4","ЛАБ","АУД"))), "")
            # Предмет
            link = tag.find("a")
            subject = link.get_text(strip=True) if link else (text[:60] if len(text) > 5 else "")

            if subject and len(subject) > 3:
                entry = f"\n📌 {current_date}"
                entry += f"\n   📚 {subject}"
                if time_str:
                    entry += f"\n   🕐 {time_str}"
                if room_str:
                    entry += f"  |  🏛 {room_str}"
                exam_entries.append(entry)
                current_date = ""

        # Консультація
        if "консультація" in text.lower() and exam_entries:
            exam_entries[-1] += f"\n   💬 {text}"

    if not exam_entries:
        # Якщо не вдалось розпарсити — показуємо PDF і посилання
        return (
            f"📝 Розклад екзаменів — {display_name}\n\n"
            f"Розклад доступний на офіційному сайті ТНТУ.\n"
            f"Натисни щоб відкрити:\n\n"
            f"🔗 {url}"
        )

    result = [f"📝 Розклад екзаменів — {display_name}\n"]
    result.extend(exam_entries[:15])
    result.append(f"\n\n🔗 Повний розклад: {url}")
    return "\n".join(result)


def get_schedule_pdfs(faculty_code: str, group_name: str) -> str:
    """Повертає PDF посилання на розклад занять."""
    data = get_faculty_data(faculty_code)
    pdfs = data.get("pdf_links", [])
    url  = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"

    if not pdfs:
        return (
            f"📅 Розклад занять — {group_name}\n\n"
            f"PDF-файли ще не завантажено або розклад на сайті.\n\n"
            f"🔗 {url}"
        )

    # Фільтруємо за групою якщо можливо
    group_prefix = "".join(c for c in group_name if c.isalpha())[:2].upper()
    relevant = [(t, u) for t, u in pdfs if group_prefix in t.upper() or "PDF" in t.upper()]
    show_pdfs = relevant if relevant else pdfs

    lines = [f"📅 Розклад занять — {group_name}\n"]
    for title, pdf_url in show_pdfs[:6]:
        lines.append(f"📄 {title}\n🔗 {pdf_url}\n")

    lines.append(f"📋 Всі розклади факультету:\n{url}")
    return "\n".join(lines)