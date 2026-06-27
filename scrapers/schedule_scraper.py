import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}
MONTHS  = ["січня","лютого","березня","квітня","травня","червня",
           "липня","серпня","вересня","жовтня","листопада","грудня"]
NAV_SKIP = ["факультет","студенту","головна","меню","copyright",
            "пошук","новини","powered","університет","©"]


def _fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        return BeautifulSoup(r.text, "html.parser") if r.status_code == 200 else None
    except Exception:
        return None


def _is_date(text: str) -> tuple[bool, str]:
    """Перевіряє чи рядок є датою і повертає (True, 'дата') або (False, '')."""
    words = text.strip().split()
    for i, w in enumerate(words):
        if any(m in w.lower() for m in MONTHS) and i > 0 and words[i-1].isdigit():
            date_str = " ".join(words[max(0,i-1):i+2] if i+1 < len(words) and words[i+1].isdigit() else words[max(0,i-1):i+1])
            return True, date_str
    return False, ""


def _is_room(text: str) -> bool:
    """Аудиторія: К1-101, К2-234, Лаб.5 тощо."""
    t = text.strip().upper()
    if len(t) > 15: return False
    return (t.startswith(("К1","К2","К3","К4","К5","ЛАБ","АУД"))
            and any(c.isdigit() for c in t))


def _is_time(text: str) -> bool:
    import re
    return bool(re.match(r'^\d{1,2}:\d{2}$', text.strip()))


def get_faculty_data(faculty_code: str) -> dict:
    url  = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    soup = _fetch(url)
    if not soup:
        return {"groups_by_course": {}, "pdf_links": []}

    gbc, pdfs = {}, []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            title = a.get_text(strip=True) or "Розклад"
            full  = href if href.startswith("http") else urljoin(TNTU_BASE_URL+"/", href)
            if full not in [u for _,u in pdfs]:
                pdfs.append((title[:100], full))

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "?p=uk/schedule&s=" not in href: continue
        code = href.split("&s=")[-1]
        if code in ("fmt","fpt","fis","fem",faculty_code): continue
        if not any(c.isdigit() for c in code): continue
        name = a.get_text(strip=True).split("(")[0].strip()
        if not name or len(name) > 15: continue
        digits = "".join(filter(str.isdigit, name))
        if len(digits) >= 2:
            key = f"{digits[0]} курс"
            gbc.setdefault(key, [])
            if (name, code) not in gbc[key]:
                gbc[key].append((name, code))

    return {"groups_by_course": dict(sorted(gbc.items())), "pdf_links": pdfs[:20]}


def get_exam_schedule(group_code: str, group_name: str = "") -> str:
    url     = f"{TNTU_BASE_URL}/?p=uk/schedule&s={group_code}"
    display = group_name or group_code.split("-")[-1].upper()
    soup    = _fetch(url)
    if not soup:
        return (f"❌ Не вдалося завантажити розклад.\n\n"
                f"🔗 {url}")

    # Видаляємо навігацію
    for tag in soup.find_all(["nav","header","aside","footer","script","style"]):
        tag.decompose()

    content = (soup.find("main") or soup.find("div", {"id":"content"})
               or soup.find("div", class_=lambda c: c and "content" in c.lower())
               or soup)

    # ── Крок 1: збираємо всі предмети (посилання dl.tntu.edu.ua) ─────────────
    subject_by_tag: dict = {}  # id(tag) → назва предмету
    all_links = content.find_all("a", href=True)
    for a in all_links:
        href = a["href"]
        txt  = a.get_text(strip=True)
        # Предмети — посилання на dl.tntu або довгий текст що не є аудиторією
        if ("dl.tntu" in href or "bounce.php" in href) and txt and not _is_room(txt):
            subject_by_tag[id(a)] = txt

    # ── Крок 2: проходимо всі теги і збираємо структуру ─────────────────────
    entries  = []
    cur_date = ""
    cur_subj = ""
    cur_time = ""
    cur_room = ""
    consults = []

    def flush(d, s, t, r, cs):
        if d and s:
            e = f"📌 <b>{d}</b>\n"
            e += f"   📚 {s}\n"
            if t: e += f"   🕐 {t}"
            if r: e += f"  ·  🏛 {r}"
            for c in cs:
                e += f"\n   💬 <i>{c}</i>"
            return e
        return ""

    for tag in content.find_all(["h2","h3","h4","p","li","div","td","br"]):
        text = " ".join(tag.get_text().split()).strip()
        if not text or len(text) > 400:
            continue
        if any(s in text.lower() for s in NAV_SKIP):
            continue

        # Перевіряємо чи є в тезі посилання-предмет
        found_subj = ""
        for a in tag.find_all("a", href=True):
            if id(a) in subject_by_tag:
                found_subj = subject_by_tag[id(a)]
                break

        # Дата
        is_d, date_val = _is_date(text)
        if is_d:
            if cur_date and cur_subj:
                e = flush(cur_date, cur_subj, cur_time, cur_room, consults)
                if e: entries.append(e)
            cur_date, cur_subj, cur_time, cur_room, consults = date_val, "", "", "", []
            continue

        # Консультація
        if "консультація" in text.lower() and cur_date:
            consults.append(text)
            continue

        # Предмет (з посилання)
        if found_subj:
            if cur_date and cur_subj:
                e = flush(cur_date, cur_subj, cur_time, cur_room, consults)
                if e: entries.append(e)
                cur_subj, cur_time, cur_room, consults = "", "", "", []
            cur_subj = found_subj
            # Час і аудиторія можуть бути в тому ж тезі
            for w in text.split():
                if _is_time(w) and not cur_time:
                    cur_time = w
                elif _is_room(w) and not cur_room:
                    cur_room = w
            continue

        # Час
        if _is_time(text) and cur_date and not cur_time:
            cur_time = text
            continue

        # Аудиторія
        if _is_room(text) and cur_date and not cur_room:
            cur_room = text
            continue

        # Рядок що містить і час і аудиторію
        if cur_date:
            words = text.split()
            for w in words:
                if _is_time(w) and not cur_time:
                    cur_time = w
                elif _is_room(w) and not cur_room:
                    cur_room = w

    # Останній запис
    if cur_date and cur_subj:
        e = flush(cur_date, cur_subj, cur_time, cur_room, consults)
        if e: entries.append(e)

    if not entries:
        return (f"📝 <b>Розклад екзаменів — {display}</b>\n\n"
                f"Розклад ще не опубліковано або доступний тільки на сайті.\n\n"
                f"🔗 <a href=\"{url}\">Відкрити на сайті ТНТУ</a>")

    result = [f"📝 <b>Розклад екзаменів — {display}</b>\n"]
    result.extend(entries[:15])
    result.append(f"\n🔗 <a href=\"{url}\">Повний розклад на сайті ТНТУ</a>")
    return "\n".join(result)


def get_schedule_pdfs(faculty_code: str, group_name: str) -> str:
    data = get_faculty_data(faculty_code)
    pdfs = data.get("pdf_links", [])
    url  = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"

    # Точне співпадіння по назві групи
    exact = [(t, u) for t, u in pdfs if group_name.upper() in t.upper()]

    # Якщо не знайшли — шукаємо по курсу (перша цифра)
    if not exact:
        digits = "".join(c for c in group_name if c.isdigit())
        course = digits[0] if digits else ""
        # Шукаємо PDF де є груп того ж курсу (напр. СП-11, СА-11...)
        prefix = "".join(c for c in group_name if c.isalpha())[:2].upper()
        exact = [(t, u) for t, u in pdfs
                 if prefix in t.upper() and course in t]

    show = exact if exact else pdfs[:6]
    found_msg = (f"Знайдено <b>{len(exact)}</b> файл(ів) для групи <b>{group_name}</b>:"
                 if exact else
                 f"<i>Розклади для факультету (файл вашої групи шукайте в списку):</i>")

    if not pdfs:
        return (f"📅 <b>Розклад занять — {group_name}</b>\n\n"
                f"PDF файли не знайдено.\n🔗 <a href=\"{url}\">Сайт ТНТУ</a>")

    lines = [f"📅 <b>Розклад занять — {group_name}</b>\n", found_msg, ""]
    for title, link in show:
        lines.append(f"📄 {title}\n🔗 {link}\n")
    lines.append(f"📋 <a href=\"{url}\">Всі розклади факультету</a>")
    return "\n".join(lines)