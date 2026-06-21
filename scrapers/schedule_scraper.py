import requests
from bs4 import BeautifulSoup
from config import TNTU_BASE_URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TNTU-Bot/1.0)"
}


def get_faculty_groups(faculty_code: str) -> dict:
    """
    Повертає словник курс → список груп для заданого факультету.
    Наприклад: {"1 курс": [("СП-11", "sp11"), ("СП-12", "sp12")], ...}
    """
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # Знаходимо всі посилання на групи — вони мають href з &s=-
    group_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "?p=uk/schedule&s=-" in href:
            group_code = href.split("&s=-")[-1]          # наприклад: sp11
            group_name = a.text.strip().split(" ")[0]    # наприклад: СП-11
            if group_name and group_code:
                group_links.append((group_name, group_code))

    # Групуємо по курсах — перша цифра в коді групи це курс
    # СП-11 → 1 курс, СП-21 → 2 курс і т.д.
    courses = {}
    for name, code in group_links:
        # Визначаємо курс по другій цифрі назви групи (СП-11 → 1)
        digits = "".join(filter(str.isdigit, name))
        if len(digits) >= 2:
            course_num = digits[0]
            course_key = f"{course_num} курс"
            if course_key not in courses:
                courses[course_key] = []
            if (name, code) not in courses[course_key]:
                courses[course_key].append((name, code))

    # Сортуємо курси
    return dict(sorted(courses.items()))


def get_exam_schedule(group_code: str) -> str:
    """
    Повертає розклад екзаменів для групи у вигляді відформатованого тексту.
    """
    url = f"{TNTU_BASE_URL}/?p=uk/schedule&s=-{group_code}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
    except requests.RequestException:
        return "❌ Не вдалося отримати розклад. Спробуй пізніше."

    soup = BeautifulSoup(response.text, "html.parser")

    # Знаходимо заголовок групи (h2)
    group_title = ""
    h2 = soup.find("h2")
    if h2:
        group_title = h2.text.strip()

    # Знаходимо секції розкладу (h3)
    result_parts = [f"📝 *Розклад для групи {group_title}*\n"]
    current_section = None
    found_content = False

    # Шукаємо в основному контенті після навігації
    # Контент після другого <h2> (перший — назва університету)
    content_area = soup.find_all(["h2", "h3", "p", "ul", "li", "strong", "a"])

    # Парсимо блоки після заголовка групи
    in_schedule = False
    current_date = ""
    entries = []

    for tag in soup.find_all(["h2", "h3", "div", "p", "li", "ul"]):
        text = tag.get_text(separator=" ", strip=True)

        # Знаходимо заголовок групи
        if tag.name == "h2" and group_title and group_title in text:
            in_schedule = True
            continue

        if not in_schedule:
            continue

        # Секції
        if tag.name == "h3":
            if "екзамен" in text.lower():
                current_section = "📅 *Розклад екзаменів*"
                result_parts.append(f"\n{current_section}")
                found_content = True
            elif "повторне" in text.lower():
                current_section = "🔁 *Повторне оцінювання*"
                result_parts.append(f"\n{current_section}")
            elif "занять" in text.lower() or "заняття" in text.lower():
                break  # далі вже не розклад екзаменів

        # Шукаємо дату і предмет
        if tag.name == "p" or tag.name == "li":
            # Дата — рядок що містить тільки дату (наприклад "19 червня")
            if _is_date_line(text):
                current_date = text.strip()

            # Предмет — є посилання dl.tntu.edu.ua або жирний текст
            subject_link = tag.find("a", href=lambda h: h and "dl.tntu.edu.ua" in h)
            if subject_link and current_date:
                subject = subject_link.text.strip()
                # Час і аудиторія — шукаємо у сусідніх тегах
                time_room = _extract_time_room(tag)
                # Консультація
                consult = _extract_consultation(tag)

                entry = f"\n📌 *{current_date}*\n   📚 {subject}"
                if time_room:
                    entry += f"\n   🕐 {time_room}"
                if consult:
                    entry += f"\n   💬 Консультація: {consult}"
                result_parts.append(entry)
                found_content = True
                current_date = ""

    if not found_content:
        return (
            f"📋 Група *{group_title}*\n\n"
            "Розклад екзаменів ще не розміщений або семестр ще не завершився.\n"
            f"🔗 Переглянути на сайті: {url}"
        )

    result_parts.append(f"\n\n🔗 [Відкрити на сайті ТНТУ]({url})")
    return "\n".join(result_parts)


def _is_date_line(text: str) -> bool:
    """Перевіряє чи рядок є датою (наприклад '19 червня')."""
    months = [
        "січня", "лютого", "березня", "квітня", "травня", "червня",
        "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"
    ]
    words = text.strip().split()
    return (
        len(words) == 2
        and words[0].isdigit()
        and any(m in words[1].lower() for m in months)
    )


def _extract_time_room(tag) -> str:
    """Витягує час і аудиторію з тегу."""
    parts = []
    text = tag.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        # Час: наприклад "09:00"
        if len(line) == 5 and line[2] == ":" and line[:2].isdigit():
            parts.append(line)
        # Аудиторія: наприклад "К1-101", "К2-68", "Лаб.5"
        if line.startswith("К") and "-" in line:
            parts.append(f"ауд. {line}")
    return "  ".join(parts) if parts else ""


def _extract_consultation(tag) -> str:
    """Витягує інформацію про консультацію."""
    text = tag.get_text(separator=" ", strip=True)
    if "консультація" in text.lower() or "Консультація" in text:
        idx = text.lower().find("консультація")
        return text[idx + len("консультація"):].strip().lstrip(":").strip()
    return ""
