import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}
MONTHS  = ["січня","лютого","березня","квітня","травня","червня",
           "липня","серпня","вересня","жовтня","листопада","грудня"]
SKIP    = ["факультет","студенту","головна","меню","copyright",
           "пошук","новини","powered","©","статистика","повідомити"]


def _fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        return BeautifulSoup(r.text, "html.parser") if r.status_code == 200 else None
    except Exception:
        return None


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def _is_date(text: str) -> tuple[bool, str]:
    words = text.split()
    for i, w in enumerate(words):
        wl = w.lower().rstrip(".,")
        if any(m in wl for m in MONTHS) and i > 0 and words[i-1].isdigit():
            parts = words[max(0,i-1):i+1]
            if i+1 < len(words) and words[i+1].isdigit():
                parts.append(words[i+1])
            return True, " ".join(parts)
    return False, ""


def _is_room(w: str) -> bool:
    w = w.upper().strip(".,;:")
    return (len(w) <= 12
            and any(c.isdigit() for c in w)
            and w[:2] in ("К1","К2","К3","К4","К5","ЛА","АУ","ЛБ"))


def _is_time(w: str) -> bool:
    return bool(re.match(r'^\d{1,2}:\d{2}$', w.strip()))


def get_faculty_data(faculty_code: str) -> dict:
    url  = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    soup = _fetch(url)
    if not soup:
        return {"groups_by_course": {}, "pdf_links": []}

    gbc, pdfs = {}, []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            title = _clean(a.get_text()) or "Розклад"
            full  = href if href.startswith("http") else urljoin(TNTU_BASE_URL+"/", href)
            if full not in [u for _,u in pdfs]:
                pdfs.append((title, full))
        elif "?p=uk/schedule&s=" in href:
            code = href.split("&s=")[-1]
            if code in ("fmt","fpt","fis","fem",faculty_code): continue
            if not any(c.isdigit() for c in code): continue
            name = _clean(a.get_text()).split("(")[0]
            if not name or len(name) > 15: continue
            digits = "".join(filter(str.isdigit, name))
            if len(digits) >= 2:
                key = f"{digits[0]} курс"
                gbc.setdefault(key, [])
                if (name, code) not in gbc[key]:
                    gbc[key].append((name, code))

    return {"groups_by_course": dict(sorted(gbc.items())), "pdf_links": pdfs[:20]}


def get_full_schedule(group_code: str, group_name: str,
                      faculty_code: str) -> str:
    """
    Об'єднаний розклад: екзамени (HTML) + PDF заняття — одне повідомлення.
    """
    exam_url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={group_code}"
    display  = group_name or group_code.upper()

    # ── PDF посилання для занять ──────────────────────────────────────────────
    fac_data = get_faculty_data(faculty_code)
    pdfs     = fac_data.get("pdf_links", [])
    prefix   = "".join(c for c in group_name.upper() if c.isalpha())[:2]
    rel_pdfs = [(t,u) for t,u in pdfs if prefix in t.upper()]
    show_pdfs= rel_pdfs if rel_pdfs else pdfs[:3]

    pdf_block = ""
    if show_pdfs:
        lines_p = []
        for title, link in show_pdfs[:3]:
            lines_p.append(f"📄 <a href=\"{link}\">{title[:70]}</a>")
        pdf_block = "\n".join(lines_p)

    # ── Парсимо HTML для розкладу екзаменів ──────────────────────────────────
    soup = _fetch(exam_url)
    exam_entries = []

    if soup:
        for tag in soup.find_all(["nav","header","aside","footer","script","style"]):
            tag.decompose()

        content = (soup.find("main")
                   or soup.find("div", {"id":"content"})
                   or soup)

        # Збираємо посилання на предмети (dl.tntu.edu.ua)
        subj_map: dict[int, str] = {}
        for a in content.find_all("a", href=True):
            href = a["href"]
            txt  = _clean(a.get_text())
            if ("dl.tntu" in href or "bounce" in href) and txt and not _is_room(txt):
                subj_map[id(a)] = txt

        cur_date = cur_subj = cur_time = cur_room = ""
        consults: list[str] = []

        def flush() -> str:
            if not (cur_date and cur_subj): return ""
            row = f"\n📌 <b>{cur_date}</b>\n"
            row += f"   📚 {cur_subj}\n"
            if cur_time or cur_room:
                row += "  "
                if cur_time: row += f" 🕐 {cur_time}"
                if cur_room: row += f"  ·  🏛 {cur_room}"
            for c in consults:
                row += f"\n   💬 <i>{c}</i>"
            return row

        for tag in content.find_all(["h2","h3","h4","p","li","div","td"]):
            text = _clean(tag.get_text())
            if not text or len(text) > 400: continue
            if any(s in text.lower() for s in SKIP): continue

            # Предмет з посилання
            subj_found = ""
            for a in tag.find_all("a", href=True):
                if id(a) in subj_map:
                    subj_found = subj_map[id(a)]
                    break

            # Дата
            ok, date_val = _is_date(text)
            if ok:
                e = flush()
                if e: exam_entries.append(e)
                cur_date, cur_subj, cur_time, cur_room, consults = date_val,"","","",[]
                continue

            # Консультація
            if "консультація" in text.lower() and cur_date:
                consults.append(text); continue

            # Предмет
            if subj_found:
                e = flush()
                if e: exam_entries.append(e)
                cur_subj, cur_time, cur_room, consults = subj_found,"","",[]
                for w in text.split():
                    if _is_time(w) and not cur_time: cur_time = w
                    elif _is_room(w) and not cur_room: cur_room = w
                continue

            # Час і аудиторія окремими рядками
            words = text.split()
            if len(words) <= 3 and cur_date:
                for w in words:
                    if _is_time(w) and not cur_time: cur_time = w
                    elif _is_room(w) and not cur_room: cur_room = w

        e = flush()
        if e: exam_entries.append(e)

    # ── Збираємо фінальне повідомлення ───────────────────────────────────────
    parts = [f"📋 <b>Розклад групи {display}</b>"]

    if exam_entries:
        parts.append(f"\n📝 <b>Екзамени ({len(exam_entries)}):</b>")
        parts.extend(exam_entries[:15])
        parts.append(f"\n🔗 <a href=\"{exam_url}\">Повний розклад на сайті ТНТУ</a>")
    else:
        parts.append(
            f"\n📝 <b>Розклад екзаменів:</b>\n"
            f"Дані ще не опубліковано або доступні тільки на сайті.\n"
            f"🔗 <a href=\"{exam_url}\">Відкрити на сайті ТНТУ</a>"
        )

    if pdf_block:
        parts.append(f"\n📅 <b>Розклад занять (PDF):</b>\n{pdf_block}")
    else:
        fac_url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
        parts.append(
            f"\n📅 <b>Розклад занять:</b>\n"
            f"🔗 <a href=\"{fac_url}\">Розклади факультету</a>"
        )

    return "\n".join(parts)