"""
Запуск: python -m scrapers.teachers_scraper
Джерело: tntu.edu.ua/?p=uk/structure/departments/{КОД}/staff
"""
import json, time, os, re, urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TNTU = "https://tntu.edu.ua"
OUT  = "data/teachers.json"

# ── ПОВНИЙ список кафедр із правильними кодами з tntu.edu.ua ─────────────────
# Формат: (код_на_сайті, назва_кафедри, факультет, [додаткові_субдомени])
DEPARTMENTS = [
    # ─── ФІС ─────────────────────────────────────────────────────────────────
    ("pi",  "Кафедра програмної інженерії (ПІ)",                            "ФІС",
     ["kaf-pi.tntu.edu.ua/staff2024/", "kaf-pi.tntu.edu.ua/kolektyv/"]),

    ("kn",  "Кафедра комп'ютерних наук (КН)",                               "ФІС",
     ["kaf-kn.tntu.edu.ua/personal-kafedry/", "kaf-kn.tntu.edu.ua/kolektyv/"]),

    ("ks",  "Кафедра комп'ютерних систем та мереж (КС)",                    "ФІС",
     ["kaf-ks.tntu.edu.ua/staff/", "kaf-ks.tntu.edu.ua/kolektyv/"]),

    ("kb",  "Кафедра кібербезпеки (КБ)",                                    "ФІС",
     ["kaf-kb.tntu.edu.ua/kolektyv/", "kaf-kb.tntu.edu.ua/staff/"]),

    ("sa",  "Кафедра систем штучного інтелекту та аналізу даних (СА)",      "ФІС",
     ["kaf-sa.tntu.edu.ua/kolektyv/", "kaf-sa.tntu.edu.ua/staff/"]),

    ("mm",  "Кафедра інформатики та матем. моделювання (ММ)",               "ФІС",
     ["kaf-mm.tntu.edu.ua/kolektyv/", "kaf-mm.tntu.edu.ua/staff/"]),

    ("mn",  "Кафедра математичних методів в інженерії (МН)",                "ФІС",
     ["kaf-mn.tntu.edu.ua/kolektyv/", "kaf-mn.tntu.edu.ua/staff/"]),

    ("fz",  "Кафедра фізики (ФЗ)",                                          "ФІС",
     ["physics.tntu.edu.ua/kolektyv/", "physics.tntu.edu.ua/staff/"]),

    ("is",  "Кафедра інформаційної діяльності та соціальних наук (ІС)",     "ФІС",
     ["kaf-is.tntu.edu.ua/kolektyv/", "kaf-is.tntu.edu.ua/staff/"]),

    ("ui",  "Кафедра української та іноземних мов (УІМ)",                   "ФІС",
     ["ui.tntu.edu.ua/stuff/", "ui.tntu.edu.ua/stuff", "ui.tntu.edu.ua/kolektyv/"]),

    ("fi",  "Кафедра фізичного виховання і спорту (ФВС)",                   "ФІС",
     ["kaf-fi.tntu.edu.ua/kolektyv/", "kaf-fi.tntu.edu.ua/staff/"]),

    # ─── ФПТ ─────────────────────────────────────────────────────────────────
    ("kt",  "Кафедра комп'ютерно-інтегрованих технологій (КТ)",             "ФПТ",
     ["kt.tntu.edu.ua/test-3/", "kt.tntu.edu.ua/kolektyv/"]),

    ("bs",  "Кафедра біотехнічних систем (БС)",                             "ФПТ",
     ["kaf-bs.tntu.edu.ua/kolektyv/", "kaf-bs.tntu.edu.ua/staff/"]),

    ("em",  "Кафедра електричної інженерії (ЕМ)",                           "ФПТ",
     ["kaf-em.tntu.edu.ua/kolektyv/", "kaf-em.tntu.edu.ua/staff/"]),

    ("ra",  "Кафедра радіотехнічних систем (РА)",                           "ФПТ",
     ["kaf-ra.tntu.edu.ua/kolektyv/", "kaf-ra.tntu.edu.ua/staff/"]),

    ("rb",  "Кафедра приладів і контрольно-вимірювальних систем (РБ)",      "ФПТ",
     ["kaf-rb.tntu.edu.ua/kolektyv/", "kaf-rb.tntu.edu.ua/staff/"]),

    # ─── ФМТ ─────────────────────────────────────────────────────────────────
    ("vi",  "Кафедра конструювання верстатів, інструментів та машин (ВІ)",  "ФМТ",
     ["kaf-vi.tntu.edu.ua/home/vykladachi/", "kaf-vi.tntu.edu.ua/vykladachi/"]),

    ("av",  "Кафедра автоматизації технологічних процесів і виробництв (АВ)", "ФМТ",
     ["kaf-av.tntu.edu.ua/index.php/mn-main/mn-workers",
      "kaf-av.tntu.edu.ua/kolektyv/"]),

    ("mb",  "Кафедра будівельної механіки (МБ)",                            "ФМТ",
     ["kaf-mb.tntu.edu.ua/kolektyv/", "kaf-mb.tntu.edu.ua/staff/"]),

    ("inp", "Кафедра харчових технологій та хімії (ІНП)",                   "ФМТ",
     ["kaf-inp.tntu.edu.ua/kolektyv/", "kaf-inp.tntu.edu.ua/staff/"]),

    ("tp",  "Кафедра транспортних технологій та механіки (ТП)",             "ФМТ",
     ["kaf-tp.tntu.edu.ua/kolektyv/", "kaf-tp.tntu.edu.ua/staff/"]),

    ("tm",  "Кафедра технічної механіки та сільськогосподарських машин (ТМ)", "ФМТ",
     ["kaf-tm.tntu.edu.ua/kolektyv/", "kaf-tmi.tntu.edu.ua/kolektyv/"]),

    # ─── ФЕМ ─────────────────────────────────────────────────────────────────
    ("ef",  "Кафедра економіки та фінансів (ЕФ)",                           "ФЕМ",
     ["kaf-ef.tntu.edu.ua/personal/", "kaf-ef.tntu.edu.ua/kolektyv/"]),

    ("oa",  "Кафедра бухгалтерського обліку та аудиту (ОА)",                "ФЕМ",
     ["kaf-oa.tntu.edu.ua/kolektyv/", "kaf-oa.tntu.edu.ua/staff/"]),

    ("mk",  "Кафедра промислового маркетингу (МК)",                         "ФЕМ",
     ["kaf-pm.tntu.edu.ua/kolektyv/", "kaf-mk.tntu.edu.ua/kolektyv/"]),

    ("ma",  "Кафедра менеджменту та адміністрування (МА)",                  "ФЕМ",
     ["kaf-ma.tntu.edu.ua/kolektyv/", "kaf-ma.tntu.edu.ua/staff/"]),

    ("uid", "Кафедра управління інноваційною діяльністю та сферою послуг (УІД)", "ФЕМ",
     ["kaf-mp.tntu.edu.ua/stuff", "kaf-mp.tntu.edu.ua/stuff/",
      "kaf-uid.tntu.edu.ua/kolektyv/"]),

    ("be",  "Кафедра економічної кібернетики (БЕ)",                         "ФЕМ",
     ["kaf-be.tntu.edu.ua/kolektyv/", "kaf-be.tntu.edu.ua/staff/"]),
]

SKIP = {
    "кафедра","факультет","університет","відділ","центр","лабораторія",
    "інститут","персонал","колектив","навчання","розклад","контакти",
    "головна","новини","меню","пошук","архів","copyright","all","rights",
    "reserved","menu","home","close","search","науково","педагогічний",
    "навчально","допоміжний","powered","wordpress","при використанні",
}

POSITION_KW = [
    "проф","доц","асист","викладач","зав.","д-р","канд","PhD","Ph.D","доктор",
    "к.т.н","к.е.н","к.ф.-м.н","д.т.н","д.е.н","д.ф.-м.н","к.пед",
    "старший","ст.викл","завідувач",
]


def make_schedule_url(pib: str) -> str:
    return f"{TNTU}/?p=uk/schedule&t={urllib.parse.quote(pib)}"


def fetch(url: str) -> BeautifulSoup | None:
    try:
        if not url.startswith("http"):
            url = "https://" + url
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = "utf-8"
        if r.status_code != 200 or len(r.text) < 400:
            return None
        low = r.text.lower()
        if any(x in low[:600] for x in ["404","не знайдено","page not found"]):
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def is_pib(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 80 or len(text) < 5:
        return False
    words = text.split()
    if len(words) < 2 or len(words) > 5:
        return False
    if not words[0][0].isupper():
        return False
    lower = text.lower()
    if any(s in lower for s in SKIP):
        return False
    return sum(1 for w in words if w and w[0].isupper()) >= 2


def get_position(text: str, pib: str) -> str:
    clean = text.replace(pib, "").strip()
    parts = [p.strip(" ,.") for p in re.split(r"[,\n]", clean)]
    pos = [p for p in parts if p and any(kw.lower() in p.lower() for kw in POSITION_KW)]
    return ", ".join(pos[:3])


def get_email(text: str) -> str:
    m = re.search(r"[\w.\-]+@[\w.\-]+\.(edu\.ua|com|ua)", text)
    return m.group(0) if m else ""


# ── Парсер сторінок з ГОЛОВНОГО САЙТУ ТНТУ ───────────────────────────────────
def parse_main_site(dept_code: str, dept_name: str, faculty: str) -> list[dict]:
    """
    Парсить https://tntu.edu.ua/?p=uk/structure/departments/{code}/staff
    Там дані у форматі:
    <li>Прізвище Ім'я По-батькові, к.т.н., доцент, завідувач кафедри</li>
    """
    url = f"{TNTU}/?p=uk/structure/departments/{dept_code}/staff"
    soup = fetch(url)
    if not soup:
        return []

    found: dict[str, dict] = {}

    for li in soup.find_all("li"):
        text = re.sub(r"\s+", " ", li.get_text(" ", strip=True))
        if len(text) < 8 or len(text) > 300:
            continue

        parts = text.split(",", 1)
        pib = parts[0].strip()
        position = parts[1].strip() if len(parts) > 1 else ""

        if not is_pib(pib) or pib in found:
            continue

        found[pib] = {
            "name": pib,
            "position": position,
            "department": dept_name,
            "faculty": faculty,
            "email": get_email(text),
            "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    return list(found.values())


# ── Парсер піддоменів кафедр ──────────────────────────────────────────────────
def parse_subdomain(url: str, dept_name: str, faculty: str) -> list[dict]:
    soup = fetch(url)
    if not soup:
        return []

    found: dict[str, dict] = {}

    # Спосіб 1 — посилання ?p=uk/schedule&t=ПІБ
    for a in soup.find_all("a", href=True):
        if "?p=uk/schedule&t=" not in a["href"]:
            continue
        try:
            pib = urllib.parse.unquote(a["href"].split("&t=")[-1])
        except Exception:
            continue
        if not is_pib(pib) or pib in found:
            continue
        pt = a.parent.get_text(" ", strip=True) if a.parent else ""
        found[pib] = {
            "name": pib,
            "position": get_position(pt, pib),
            "department": dept_name, "faculty": faculty,
            "email": get_email(pt), "courses": [],
            "schedule_url": make_schedule_url(pib),
        }
    if found:
        return list(found.values())

    # Спосіб 2 — <strong>/<b>/<h3>/<h4>
    for tag in soup.find_all(["strong", "b", "h3", "h4", "h5"]):
        pib = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
        if not is_pib(pib) or pib in found:
            continue
        pt = tag.parent.get_text(" ", strip=True) if tag.parent else pib
        found[pib] = {
            "name": pib,
            "position": get_position(pt, pib),
            "department": dept_name, "faculty": faculty,
            "email": get_email(pt), "courses": [],
            "schedule_url": make_schedule_url(pib),
        }
    if found:
        return list(found.values())

    # Спосіб 3 — <li>/<p>/<td> з ключовим словом посади
    for tag in soup.find_all(["li", "p", "td"]):
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
        if len(text) < 8 or len(text) > 250:
            continue
        if not any(kw.lower() in text.lower() for kw in POSITION_KW):
            continue
        before = text.split(",")[0].strip()
        words = [w for w in before.split() if w and w[0].isupper()][:4]
        if len(words) < 2:
            continue
        pib = " ".join(words)
        if not is_pib(pib) or pib in found:
            continue
        found[pib] = {
            "name": pib,
            "position": get_position(text, pib),
            "department": dept_name, "faculty": faculty,
            "email": get_email(text), "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    return list(found.values())


def run():
    print("=" * 70)
    print("  Скрапер викладачів ТНТУ")
    print("  Джерело 1: tntu.edu.ua/structure/departments/{КОД}/staff")
    print("  Джерело 2: піддомени кафедр")
    print("=" * 70)

    all_t, failed = [], []

    for dept_code, dept_name, faculty, extra_urls in DEPARTMENTS:
        print(f"\n[{faculty}] {dept_name[:52]}...")

        # 1. Спробуємо головний сайт ТНТУ (найнадійніший)
        teachers = parse_main_site(dept_code, dept_name, faculty)
        if teachers:
            print(f"    OK (main site) -> {len(teachers)} ос.")
            all_t.extend(teachers)
            time.sleep(0.3)
            continue

        # 2. Спробуємо піддомени
        found_on_sub = False
        for url in extra_urls:
            teachers = parse_subdomain(url, dept_name, faculty)
            if teachers:
                print(f"    OK ({url}) -> {len(teachers)} ос.")
                all_t.extend(teachers)
                found_on_sub = True
                break
            time.sleep(0.2)

        if not found_on_sub:
            failed.append(dept_name)
            print("    FAIL")

        time.sleep(0.4)

    # Унікальні, відсортовані
    seen, unique = set(), []
    for t in all_t:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique.append(t)
    unique.sort(key=lambda t: (t["faculty"], t["department"], t["name"]))

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"  Збережено: {len(unique)} викладачів -> {OUT}")
    if failed:
        print(f"\n  Не знайдено ({len(failed)} кафедр):")
        for n in failed:
            print(f"    - {n}")
    print("=" * 70)


if __name__ == "__main__":
    run()