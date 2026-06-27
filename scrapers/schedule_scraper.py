import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}
MONTHS = ["січня","лютого","березня","квітня","травня","червня",
          "липня","серпня","вересня","жовтня","листопада","грудня"]


def _fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        return BeautifulSoup(r.text, "html.parser") if r.status_code == 200 else None
    except Exception:
        return None


def get_faculty_data(faculty_code: str) -> dict:
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    soup = _fetch(url)
    if not soup:
        return {"groups_by_course": {}, "pdf_links": []}

    groups_by_course: dict = {}
    pdf_links: list = []

    # PDF посилання
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            title = a.get_text(strip=True) or "Розклад"
            full = href if href.startswith("http") else urljoin(TNTU_BASE_URL + "/", href)
            if full not in [u for _, u in pdf_links]:
                pdf_links.append((title[:100], full))

    # Групи
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "?p=uk/schedule&s=" not in href:
            continue
        code_part = href.split("&s=")[-1]
        if code_part in ("fmt","fpt","fis","fem", faculty_code):
            continue
        if not any(c.isdigit() for c in code_part):
            continue
        name = a.get_text(strip=True).split("(")[0].strip()
        if not name or len(name) > 15:
            continue
        digits = "".join(filter(str.isdigit, name))
        if len(digits) >= 2:
            key = f"{digits[0]} курс"
            groups_by_course.setdefault(key, [])
            entry = (name, code_part)
            if entry not in groups_by_course[key]:
                groups_by_course[key].append(entry)

    return {"groups_by_course": dict(sorted(groups_by_course.items())),
            "pdf_links": pdf_links[:20]}


def get_exam_schedule(group_code: str, group_name: str = "") -> str:
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={group_code}"
    display = group_name or group_code.split("-")[-1].upper()
    soup = _fetch(url)
    if not soup:
        return (f"❌ Не вдалося завантажити розклад.\n\n"
                f"🔗 {url}")

    # Видаляємо навігацію
    for tag in soup.find_all(["nav","header","aside","footer"]):
        tag.decompose()

    entries = []
    current_date = ""

    content = (soup.find("main") or soup.find("div", {"id":"content"})
               or soup.find("div", {"class":"content"}) or soup)

    for tag in content.find_all(["h2","h3","h4","p","li","div","td"]):
        text = " ".join(tag.get_text().split()).strip()
        if not text or len(text) > 500:
            continue

        # Пропуск навігаційних рядків
        skip = ["факультет","студенту","головна","меню","copyright","пошук",
                "новини","powered","університет"]
        if any(s in text.lower() for s in skip):
            continue

        # Дата типу "19 червня" або "19 червня 2026"
        words = text.split()
        if (len(words) >= 2 and words[0].isdigit()
                and any(m in words[1].lower() for m in MONTHS)):
            current_date = " ".join(words[:3] if len(words) >= 3 and words[2].isdigit() else words[:2])
            continue

        link = tag.find("a", href=lambda h: h and "dl.tntu" in h)
        has_time = any(":" in w and len(w) == 5 and w[:2].isdigit() for w in words)
        has_room = any(w.upper().startswith(("К1","К2","К3","К4","ЛАБ","АУД","ЛАБ.")) for w in words)

        if current_date and (link or has_time or has_room):
            subject = link.get_text(strip=True) if link else (text[:70] if len(text) > 5 else "")
            time_str = next((w for w in words if ":" in w and len(w)==5 and w[:2].isdigit()), "")
            room_str = next((w for w in words if w.upper().startswith(("К1","К2","К3","К4","ЛАБ"))), "")

            if subject and len(subject) > 3:
                e = f"📌 <b>{current_date}</b>\n"
                e += f"   📚 {subject}\n"
                if time_str: e += f"   🕐 {time_str}"
                if room_str: e += f"  |  🏛 {room_str}"
                entries.append(e)
                current_date = ""

        if "консультація" in text.lower() and entries:
            entries[-1] += f"\n   💬 {text}"

    if not entries:
        return (f"📝 <b>Розклад екзаменів — {display}</b>\n\n"
                f"Дані ще не опубліковано або доступні тільки на сайті.\n\n"
                f"🔗 <a href=\"{url}\">Відкрити на сайті ТНТУ</a>")

    result = [f"📝 <b>Розклад екзаменів — {display}</b>\n"]
    result.extend(entries[:15])
    result.append(f"\n🔗 <a href=\"{url}\">Повний розклад на сайті ТНТУ</a>")
    return "\n".join(result)


def get_schedule_pdfs(faculty_code: str, group_name: str) -> str:
    data = get_faculty_data(faculty_code)
    pdfs = data.get("pdf_links", [])
    url  = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"

    # Фільтр по назві групи
    prefix = "".join(c for c in group_name.upper() if c.isalpha())[:2]
    course_digit = "".join(c for c in group_name if c.isdigit())[:1]

    relevant = []
    for title, link in pdfs:
        t_up = title.upper()
        # Шукаємо PDF де згадується схожа назва групи або курс
        if prefix in t_up or (course_digit and f"-{course_digit}" in t_up):
            relevant.append((title, link))

    show = relevant if relevant else pdfs[:6]

    if not show:
        return (f"📅 <b>Розклад занять — {group_name}</b>\n\n"
                f"PDF файли не знайдено.\n"
                f"🔗 <a href=\"{url}\">Переглянь на сайті ТНТУ</a>")

    lines = [f"📅 <b>Розклад занять — {group_name}</b>\n"]
    if relevant:
        lines.append(f"<i>Знайдено {len(relevant)} файл(ів) для вашої групи:</i>\n")
    else:
        lines.append(f"<i>Розклади для факультету:</i>\n")

    for title, link in show:
        lines.append(f"📄 {title}\n🔗 {link}\n")

    lines.append(f"📋 <a href=\"{url}\">Всі розклади факультету</a>")
    return "\n".join(lines)