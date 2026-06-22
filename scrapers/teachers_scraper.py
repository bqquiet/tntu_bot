"""
Скрапер для збору викладачів з офіційного сайту ТНТУ.
Запускається окремо через: python -m scrapers.teachers_scraper
Оновлює data/teachers.json актуальними даними з сайту.
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"}

# Всі кафедри університету з їх кодами і факультетами
DEPARTMENTS = [
    # ФІС — Факультет комп'ютерно-інформаційних систем і програмної інженерії
    ("pi",  "Кафедра програмної інженерії (ПІ)",                       "ФІС"),
    ("kn",  "Кафедра комп'ютерних наук (КН)",                          "ФІС"),
    ("ks",  "Кафедра комп'ютерних систем та мереж (КС)",               "ФІС"),
    ("kb",  "Кафедра кібербезпеки (КБ)",                               "ФІС"),
    ("sa",  "Кафедра систем штучного інтелекту та аналізу даних (СА)", "ФІС"),
    ("mm",  "Кафедра математичних методів в інженерії (ММ)",           "ФІС"),
    ("fz",  "Кафедра фізики (ФЗ)",                                     "ФІС"),
    ("imm", "Кафедра інформатики та математичного моделювання (ІМ)",   "ФІС"),
    ("ui",  "Кафедра української та іноземних мов (УІМ)",              "ФІС"),

    # ФПТ — Факультет прикладних інформаційних технологій та електроінженерії
    ("kt",  "Кафедра комп'ютерно-інтегрованих технологій (КТ)",        "ФПТ"),
    ("em",  "Кафедра електричної інженерії (ЕМ)",                      "ФПТ"),
    ("ra",  "Кафедра радіотехнічних систем (РА)",                      "ФПТ"),
    ("rb",  "Кафедра приладів і контрольно-вимірювальних систем (РБ)", "ФПТ"),

    # ФМТ — Факультет інженерії машин, споруд та технологій
    ("ma",  "Кафедра інженерії машин та обладнання (МА)",              "ФМТ"),
    ("mb",  "Кафедра будівельної механіки (МБ)",                       "ФМТ"),
    ("mg",  "Кафедра харчової біотехнології та хімії (МГ)",            "ФМТ"),
    ("mp",  "Кафедра транспортних технологій та механіки (МП)",        "ФМТ"),

    # ФЕМ — Факультет економіки та менеджменту
    ("bо",  "Кафедра бухгалтерського обліку та аудиту",                "ФЕМ"),
    ("pm",  "Кафедра промислового маркетингу",                         "ФЕМ"),
    ("me",  "Кафедра менеджменту та адміністрування",                  "ФЕМ"),
    ("uid", "Кафедра управління інноваційною діяльністю",              "ФЕМ"),
]


def scrape_department_staff(dept_code: str, dept_name: str, faculty: str) -> list[dict]:
    """Парсить сторінку викладачів однієї кафедри."""
    url = f"{TNTU_BASE_URL}/?p=uk/structure/departments/{dept_code}/staff"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        if response.status_code != 200:
            return []
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    teachers = []

    # Шукаємо контентну зону (після навігації)
    # Структура: <li>Прізвище Ім'я По-батькові, к.т.н., доцент</li>
    content_started = False
    for tag in soup.find_all(["h2", "h3", "li", "p"]):
        text = tag.get_text(separator=" ", strip=True)

        # Починаємо після заголовка "Науково-педагогічний персонал" або "Персонал"
        if tag.name in ("h2", "h3") and any(
            kw in text.lower() for kw in ["персонал", "склад", "викладач"]
        ):
            content_started = True
            continue

        # Зупиняємось на іншому великому заголовку
        if content_started and tag.name == "h2" and "персонал" not in text.lower():
            break

        if not content_started:
            continue

        # Парсимо рядок: "Прізвище Ім'я По-батькові, посада"
        if tag.name == "li" and len(text) > 10:
            teacher = _parse_teacher_line(text, dept_name, faculty)
            if teacher:
                teachers.append(teacher)

    return teachers


def _parse_teacher_line(text: str, dept_name: str, faculty: str) -> dict | None:
    """Розбирає рядок 'Прізвище Ім'я По-батькові, к.т.н., доцент' на поля."""
    # Відокремлюємо ім'я від посади через кому
    parts = text.split(",", 1)
    name = parts[0].strip()

    # Перевіряємо що це схоже на ПІБ (мінімум 2 слова, починається з великої)
    words = name.split()
    if len(words) < 2 or not words[0][0].isupper():
        return None

    # Не беремо якщо схоже на назву підрозділу
    skip_keywords = ["кафедра", "відділ", "центр", "інститут", "факультет", "лабораторія"]
    if any(kw in name.lower() for kw in skip_keywords):
        return None

    position = parts[1].strip() if len(parts) > 1 else ""

    return {
        "name": name,
        "position": position,
        "department": dept_name,
        "faculty": faculty,
        "email": "",
        "courses": [],
    }


def scrape_all_teachers(output_file: str = "data/teachers.json") -> int:
    """
    Головна функція: обходить всі кафедри і зберігає викладачів у JSON.
    Повертає кількість знайдених викладачів.
    """
    all_teachers = []

    for dept_code, dept_name, faculty in DEPARTMENTS:
        print(f"  Парсимо {dept_name}...")
        teachers = scrape_department_staff(dept_code, dept_name, faculty)
        all_teachers.extend(teachers)
        time.sleep(0.5)  # пауза між запитами щоб не перевантажувати сервер

    # Видаляємо дублікати по імені
    seen = set()
    unique = []
    for t in all_teachers:
        if t["name"] not in seen:
            seen.add(t["name"])
            unique.append(t)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    return len(unique)


if __name__ == "__main__":
    print("🔄 Оновлення бази викладачів з сайту ТНТУ...")
    count = scrape_all_teachers()
    print(f"✅ Готово! Знайдено {count} викладачів. Збережено в data/teachers.json")
