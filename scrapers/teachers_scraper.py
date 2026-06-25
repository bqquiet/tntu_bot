"""
Запуск (з папки tntu_bot/):
    python -m scrapers.teachers_scraper

Обходить ВСІ кафедри ТНТУ через їхні офіційні піддомени,
витягує список викладачів і зберігає в data/teachers.json.
"""
import json, time, os, re, urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TNTU = "https://tntu.edu.ua"
OUT  = "data/teachers.json"

# ── Повний список кафедр: (субдомен, назва, факультет, [URL-шляхи сторінки персоналу]) ──
DEPARTMENTS = [
    # ─── ФІС ─────────────────────────────────────────────────────────────────
    ("kaf-pi",  "Кафедра програмної інженерії (ПІ)",                            "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/", "/team/"]),

    ("kaf-kn",  "Кафедра комп'ютерних наук (КН)",                               "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-ks",  "Кафедра комп'ютерних систем та мереж (КС)",                    "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-kb",  "Кафедра кібербезпеки (КБ)",                                    "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-sa",  "Кафедра систем штучного інтелекту та аналізу даних (СА)",      "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-mm",  "Кафедра інформатики та матем. моделювання (ММ)",               "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-mn",  "Кафедра математичних методів в інженерії (МН)",                "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-fz",  "Кафедра фізики (ФЗ)",                                          "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-is",  "Кафедра інформаційної діяльності та соціальних наук (ІС)",     "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("ui",      "Кафедра української та іноземних мов (УІМ)",                   "ФІС",
     ["/stuff/", "/stuff", "/kolektyv/", "/staff/", "/personal/", "/workers/"]),

    ("kaf-fi",  "Кафедра фізичного виховання і спорту (ФВС)",                   "ФІС",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    # ─── ФПТ ─────────────────────────────────────────────────────────────────
    ("kt",      "Кафедра комп'ютерно-інтегрованих технологій (КТ)",             "ФПТ",
     ["/test-3/", "/kolektyv/", "/kafedra/workers/", "/team-category/workers/",
      "/workers/", "/staff/", "/personal/", "/team/"]),

    ("kaf-bs",  "Кафедра біотехнічних систем (БС)",                             "ФПТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-em",  "Кафедра електричної інженерії (ЕМ)",                           "ФПТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-ra",  "Кафедра радіотехнічних систем (РА)",                           "ФПТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-rb",  "Кафедра приладів і контрольно-вимірювальних систем (РБ)",      "ФПТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    # ─── ФМТ ─────────────────────────────────────────────────────────────────
    ("kaf-vi",  "Кафедра конструювання верстатів, інструментів і машин (ВІ)",   "ФМТ",
     ["/home/vykladachi/", "/vykladachi/", "/kolektyv/",
      "/workers/", "/staff/", "/personal/"]),

    ("kaf-av",  "Кафедра автоматизації технологічних процесів (АВ)",            "ФМТ",
     ["/index.php/mn-main/mn-workers", "/kolektyv/",
      "/workers/", "/staff/", "/personal/"]),

    ("kaf-mb",  "Кафедра будівельної механіки та матеріалів (МБ)",              "ФМТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-inp", "Кафедра харчових технологій та хімії (ІНП)",                   "ФМТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-tp",  "Кафедра транспортних технологій та механіки (ТП)",             "ФМТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-tmi", "Кафедра технічної механіки та машинознавства (ТМІ)",           "ФМТ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    # ─── ФЕМ ─────────────────────────────────────────────────────────────────
    ("kaf-ef",  "Кафедра економіки та фінансів (ЕФ)",                           "ФЕМ",
     ["/personal/", "/kolektyv/", "/staff/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-bo",  "Кафедра бухгалтерського обліку та аудиту (БО)",                "ФЕМ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-pm",  "Кафедра промислового маркетингу (ПМ)",                         "ФЕМ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-ma",  "Кафедра менеджменту та адміністрування (МА)",                  "ФЕМ",
     ["/kolektyv/", "/staff/", "/personal/", "/workers/", "/sklad-kafedry/"]),

    ("kaf-mp",  "Кафедра управління інноваційною діяльністю та сферою послуг (МП)", "ФЕМ",
     ["/stuff", "/stuff/", "/kolektyv/", "/workers/", "/staff/", "/personal/"]),
]

SKIP = {
    "кафедра","факультет","університет","відділ","центр","лабораторія",
    "інститут","персонал","колектив","навчання","розклад","контакти",
    "головна","новини","меню","пошук","архів","copyright","all","rights",
    "reserved","menu","home","close","search","науково","педагогічний",
    "навчально","допоміжний","powered","wordpress",
}

POSITION_KW = [
    "проф","доц","асист","викладач","зав.","д-р","канд","PhD","доктор",
    "к.т.н","к.е.н","к.ф.-м.н","д.т.н","д.е.н","старший","ст.викл",
]


def make_schedule_url(pib: str) -> str:
    return f"{TNTU}/?p=uk/schedule&t={urllib.parse.quote(pib)}"


def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = "utf-8"
        if r.status_code != 200 or len(r.text) < 400:
            return None
        low = r.text.lower()
        if any(x in low[:600] for x in ["404","не знайдено","page not found","немає такої"]):
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
    # Мінімум 2 слова починаються з великої
    return sum(1 for w in words if w and w[0].isupper()) >= 2


def get_position(text: str, pib: str) -> str:
    clean = text.replace(pib, "").strip()
    parts = [p.strip(" ,.") for p in re.split(r"[,\n]", clean)]
    pos = [p for p in parts if p and any(kw.lower() in p.lower() for kw in POSITION_KW)]
    return ", ".join(pos[:3])


def get_email(text: str) -> str:
    m = re.search(r"[\w.\-]+@[\w.\-]+\.(edu\.ua|com|ua)", text)
    return m.group(0) if m else ""


def parse_page(soup: BeautifulSoup, dept: str, faculty: str) -> list[dict]:
    found: dict[str, dict] = {}

    # Спосіб 1 — посилання ?p=uk/schedule&t=ПІБ (найнадійніший)
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
            "department": dept, "faculty": faculty,
            "email": get_email(pt), "courses": [],
            "schedule_url": make_schedule_url(pib),
        }
    if found:
        return list(found.values())

    # Спосіб 2 — <strong>/<b>/<h3>/<h4> з ПІБ
    for tag in soup.find_all(["strong", "b", "h3", "h4", "h5"]):
        pib = re.sub(r"\s+", " ", tag.get_text(" ", strip=True))
        if not is_pib(pib) or pib in found:
            continue
        pt = tag.parent.get_text(" ", strip=True) if tag.parent else pib
        found[pib] = {
            "name": pib,
            "position": get_position(pt, pib),
            "department": dept, "faculty": faculty,
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
            "department": dept, "faculty": faculty,
            "email": get_email(text), "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    return list(found.values())


def scrape_dept(subdomain: str, dept_name: str, faculty: str, paths: list[str]) -> list[dict]:
    base = f"https://{subdomain}.tntu.edu.ua"
    for path in paths:
        soup = fetch(base + path)
        if not soup:
            continue
        teachers = parse_page(soup, dept_name, faculty)
        if teachers:
            print(f"    OK  {base + path}  ({len(teachers)} ос.)")
            return teachers
        time.sleep(0.2)
    return []


def run():
    print("=" * 68)
    print("  Скрапер викладачів ТНТУ")
    print("=" * 68)
    all_t, failed = [], []

    for subdomain, dept_name, faculty, paths in DEPARTMENTS:
        print(f"\n[{faculty}] {dept_name[:52]}...")
        teachers = scrape_dept(subdomain, dept_name, faculty, paths)
        if teachers:
            all_t.extend(teachers)
        else:
            failed.append((subdomain, dept_name))
            print("    FAIL — не знайдено жодного URL")
        time.sleep(0.4)

    # Унікальні по ПІБ
    seen, unique = set(), []
    for t in all_t:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique.append(t)

    # Сортуємо: факультет → кафедра → прізвище
    unique.sort(key=lambda t: (t["faculty"], t["department"], t["name"]))

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 68)
    print(f"  Збережено {len(unique)} викладачів -> {OUT}")
    if failed:
        print(f"\n  Не знайдено ({len(failed)} кафедр):")
        for sd, nm in failed:
            print(f"    {sd}.tntu.edu.ua  |  {nm[:50]}")
        print("\n  Порада: відкрий браузер, зайди на сайт кафедри вручну,")
        print("  знайди сторінку з персоналом і надішли URL розробнику.")
    print("=" * 68)


if __name__ == "__main__":
    run()