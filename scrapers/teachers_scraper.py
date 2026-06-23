"""
Запуск (з папки tntu_bot/):
    python -m scrapers.teachers_scraper
"""
import json, time, os, re, urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TNTU = "https://tntu.edu.ua"
OUT  = "data/teachers.json"

# ── Кафедри: (субдомен, назва, факультет, сторінки колективу) ────────────────
# Субдомени знайдені з реального сайту ТНТУ
DEPARTMENTS = [
    # ─── ФІС ─────────────────────────────────────────────────────────────
    ("kaf-kn",  "Кафедра комп'ютерних наук (КН)",                            "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/", "/team/"]),

    ("kaf-ks",  "Кафедра комп'ютерних систем та мереж (КС)",                 "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-kb",  "Кафедра кібербезпеки (КБ)",                                 "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-pi",  "Кафедра програмної інженерії (ПІ)",                          "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-mm",  "Кафедра інформатики та математичного моделювання (ММ)",      "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-mn",  "Кафедра математичних методів в інженерії (МН)",              "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-fz",  "Кафедра фізики (ФЗ)",                                        "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-is",  "Кафедра інформаційної діяльності та соціальних наук (ІС)",  "ФІС",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("ui",      "Кафедра української та іноземних мов (УІ)",                 "ФІС",
     ["/stuff/", "/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-fi",  "Кафедра фізичного виховання і спорту (ФІ)",                 "ФІС",
     ["/kolektyv/", "/workers/", "/staff/", "/personal/"]),

    # ─── ФПТ ─────────────────────────────────────────────────────────────
    ("kt",      "Кафедра комп'ютерно-інтегрованих технологій (КТ)",          "ФПТ",
     ["/test-3/", "/kolektyv/", "/kafedra/workers/", "/team-category/workers/",
      "/workers/", "/staff/", "/personal/"]),

    ("kaf-bs",  "Кафедра біотехнічних систем (БС)",                          "ФПТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-em",  "Кафедра електричної інженерії (ЕМ)",                        "ФПТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-ra",  "Кафедра радіотехнічних систем (РА)",                        "ФПТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-rb",  "Кафедра приладів і КВС (РБ)",                               "ФПТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    # ─── ФМТ ─────────────────────────────────────────────────────────────
    ("kaf-vi",  "Кафедра конструювання верстатів, інструментів та машин (ВІ)","ФМТ",
     ["/home/vykladachi/", "/vykladachi/", "/kolektyv/", "/workers/", "/staff/"]),

    ("kaf-av",  "Кафедра автоматизації технологічних процесів (АВ)",         "ФМТ",
     ["/index.php/mn-main/mn-workers", "/kolektyv/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-mb",  "Кафедра будівельної механіки (МБ)",                         "ФМТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-inp", "Кафедра харчових технологій та хімії (ІНП)",                "ФМТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-tp",  "Кафедра транспортних технологій та механіки (ТП)",          "ФМТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-tmi", "Кафедра технічної механіки та машинознавства (ТМІ)",        "ФМТ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    # ─── ФЕМ ─────────────────────────────────────────────────────────────
    ("kaf-ef",  "Кафедра економіки та фінансів (ЕФ)",                        "ФЕМ",
     ["/personal/", "/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/"]),

    ("kaf-bo",  "Кафедра бухгалтерського обліку та аудиту (БО)",             "ФЕМ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-pm",  "Кафедра промислового маркетингу (ПМ)",                      "ФЕМ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-ma",  "Кафедра менеджменту та адміністрування (МА)",               "ФЕМ",
     ["/kolektyv/", "/sklad-kafedry/", "/workers/", "/staff/", "/personal/"]),

    ("kaf-mp",  "Кафедра управління інноваційною діяльністю та сферою послуг (МП)", "ФЕМ",
     ["/stuff", "/stuff/", "/kolektyv/", "/workers/", "/staff/", "/personal/"]),
]

# ── Слова що НЕ є частиною ПІБ ───────────────────────────────────────────────
SKIP = {
    "кафедра","факультет","університет","відділ","центр","лабораторія",
    "інститут","персонал","колектив","навчання","розклад","контакти",
    "головна","новини","меню","пошук","головна","архів","викладач",
    "науково","педагогічний","навчально","допоміжний","copyright","all",
    "rights","reserved","menu","home","close","search","зав","проф",
}

POSITION_KW = [
    "проф","доц","асист","викладач","зав.","д-р","канд",
    "PhD","доктор","ректор","декан","проректор","ст.викл",
    "к.т.н","к.е.н","к.ф.-м.н","д.т.н","д.е.н","старший",
]


def make_schedule_url(pib: str) -> str:
    return f"{TNTU}/?p=uk/schedule&t={urllib.parse.quote(pib)}"


def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = "utf-8"
        if r.status_code != 200 or len(r.text) < 300:
            return None
        low = r.text.lower()
        # Відхиляємо сторінки-заглушки
        if any(x in low[:500] for x in ["404", "не знайдено", "page not found", "немає такої"]):
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def is_pib(text: str) -> bool:
    """Чи схожий рядок на ПІБ (Прізвище Ім'я По-батькові)."""
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
    # Мінімум 2 слова з великої літери
    return sum(1 for w in words if w and w[0].isupper()) >= 2


def get_position(full_text: str, pib: str) -> str:
    clean = full_text.replace(pib, "").strip()
    parts = [p.strip(" ,.") for p in re.split(r'[,\n]', clean)]
    pos = [p for p in parts if p and any(kw.lower() in p.lower() for kw in POSITION_KW)]
    return ", ".join(pos[:3])


def get_email(text: str) -> str:
    m = re.search(r'[\w.\-]+@[\w.\-]+\.(edu\.ua|com|ua)', text)
    return m.group(0) if m else ""


def parse_page(soup: BeautifulSoup, dept: str, faculty: str) -> list[dict]:
    found = {}  # name → dict

    # ── Спосіб 1: посилання з ?p=uk/schedule&t= ─────────────────────────────
    for a in soup.find_all("a", href=True):
        if "?p=uk/schedule&t=" not in a["href"]:
            continue
        try:
            pib = urllib.parse.unquote(a["href"].split("&t=")[-1])
        except Exception:
            continue
        if not is_pib(pib) or pib in found:
            continue
        parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
        found[pib] = {
            "name": pib,
            "position": get_position(parent_text, pib),
            "department": dept,
            "faculty": faculty,
            "email": get_email(parent_text),
            "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    if found:
        return list(found.values())

    # ── Спосіб 2: <strong> / <b> / <h3> / <h4> з ПІБ ────────────────────────
    for tag in soup.find_all(["strong", "b", "h3", "h4", "h5"]):
        pib = re.sub(r'\s+', ' ', tag.get_text(" ", strip=True))
        if not is_pib(pib) or pib in found:
            continue
        parent_text = tag.parent.get_text(" ", strip=True) if tag.parent else pib
        found[pib] = {
            "name": pib,
            "position": get_position(parent_text, pib),
            "department": dept,
            "faculty": faculty,
            "email": get_email(parent_text),
            "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    if found:
        return list(found.values())

    # ── Спосіб 3: рядки у <li> / <p> / <td> з ключовим словом посади ────────
    for tag in soup.find_all(["li", "p", "td", "div"]):
        text = re.sub(r'\s+', ' ', tag.get_text(" ", strip=True))
        if len(text) < 8 or len(text) > 250:
            continue
        if not any(kw.lower() in text.lower() for kw in POSITION_KW):
            continue
        # ПІБ — перші 2-4 великих слова до коми
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
            "department": dept,
            "faculty": faculty,
            "email": get_email(text),
            "courses": [],
            "schedule_url": make_schedule_url(pib),
        }

    return list(found.values())


def scrape_dept(subdomain: str, dept_name: str, faculty: str, paths: list[str]) -> list[dict]:
    base = f"https://{subdomain}.tntu.edu.ua"
    for path in paths:
        url = base + path
        soup = fetch(url)
        if not soup:
            continue
        teachers = parse_page(soup, dept_name, faculty)
        if teachers:
            print(f"    ✅ {url}  →  {len(teachers)} викладачів")
            return teachers
        time.sleep(0.2)
    return []


def run():
    print("=" * 65)
    print("  Скрапер викладачів ТНТУ")
    print("=" * 65)

    all_t, failed = [], []

    for subdomain, dept_name, faculty, paths in DEPARTMENTS:
        print(f"\n[{faculty}] {dept_name[:50]}...")
        teachers = scrape_dept(subdomain, dept_name, faculty, paths)
        if teachers:
            all_t.extend(teachers)
        else:
            failed.append(dept_name)
            print("    ❌ Не вдалось знайти сторінку")
        time.sleep(0.4)

    # Унікальні по імені
    seen, unique = set(), []
    for t in all_t:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique.append(t)

    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print(f"  ✅  Збережено {len(unique)} викладачів  →  {OUT}")
    if failed:
        print(f"\n  ⚠️   Не вдалось ({len(failed)} кафедр):")
        for n in failed:
            print(f"       - {n[:55]}")
        print("\n  Підказка: для кафедр що не знайдено — зайди на їхній сайт")
        print("  вручну і подивись точний URL сторінки з колективом.")
        print("  Зазвичай це: kaf-XX.tntu.edu.ua/kolektyv/ або /workers/")
    print("=" * 65)


if __name__ == "__main__":
    run()