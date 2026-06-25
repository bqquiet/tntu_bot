from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Всі 11 об'єктів ТНТУ впорядковані логічно
BUILDINGS = [
    # ─── Навчальні корпуси ────────────────────────────────────────────────────
    {
        "key": "corp1", "emoji": "🏛", "cat": "Навчальний корпус",
        "name": "Головний корпус (№1)",
        "address": "вул. Руська, 56",
        "work": "Пн–Пт: 8:00–20:00  |  Сб: 8:00–14:00",
        "desc": "Центральний корпус університету. Тут знаходяться ректорат, деканати більшості факультетів, основні аудиторії та актова зала.",
        "rooms": [
            "Ректорат — 2-й поверх",
            "Деканат ФІС — каб. 7, 1-й поверх",
            "Бібліотека — 1-й поверх",
            "Актова зала — 2-й поверх",
            "Аудиторії ФІС — 3–5 поверхи",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "corp2", "emoji": "🖥", "cat": "Навчальний корпус",
        "name": "Навчально-лабораторний корпус (№2)",
        "address": "вул. Руська, 56 (за головним корпусом)",
        "work": "Пн–Пт: 8:00–20:00",
        "desc": "Тут знаходяться комп'ютерні класи та лабораторії кафедр програмної інженерії, комп'ютерних систем і мереж.",
        "rooms": [
            "Комп'ютерні класи — 3–5 поверхи",
            "Лабораторії ПІ — ауд. 401–407",
            "Лабораторії КС та КН — ауд. 201–210",
            "Кафедра КТ",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "corp3", "emoji": "⚡️", "cat": "Навчальний корпус",
        "name": "Корпус ФПТ (№3)",
        "address": "вул. Микулинецька, 46",
        "work": "Пн–Пт: 8:00–19:00",
        "desc": "Корпус Факультету прикладних інформаційних технологій та електроінженерії. Кафедри електроінженерії, радіотехніки та приладів.",
        "rooms": [
            "Деканат ФПТ — 1-й поверх",
            "Радіотехнічні лабораторії",
            "Електротехнічні лабораторії",
            "Кафедра БС та ЕМ",
        ],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key": "corp4", "emoji": "⚙️", "cat": "Навчальний корпус",
        "name": "Корпус ФМТ (№4)",
        "address": "вул. Танцорова, 2",
        "work": "Пн–Пт: 8:00–18:00",
        "desc": "Корпус Факультету інженерії машин, споруд та технологій. Механічні майстерні, лабораторії матеріалознавства та машинобудування.",
        "rooms": [
            "Деканат ФМТ — 1-й поверх",
            "Механічні майстерні",
            "Лабораторія матеріалознавства",
            "Кафедри ВІ, АВ, ТМІ",
        ],
        "map": "https://maps.app.goo.gl/somelink1",
    },
    {
        "key": "corp5", "emoji": "📊", "cat": "Навчальний корпус",
        "name": "Корпус ФЕМ (№5)",
        "address": "вул. Білогірська, 50",
        "work": "Пн–Пт: 8:00–18:00",
        "desc": "Корпус Факультету економіки та менеджменту. Лекційні аудиторії та кафедри економічних дисциплін.",
        "rooms": [
            "Деканат ФЕМ — 1-й поверх",
            "Аудиторії кафедр БО, ПМ, МА",
            "Кафедра ЕФ та МП",
        ],
        "map": "https://maps.app.goo.gl/somelink2",
    },
    # ─── Об'єкти інфраструктури ───────────────────────────────────────────────
    {
        "key": "library", "emoji": "📚", "cat": "Інфраструктура",
        "name": "Наукова бібліотека",
        "address": "вул. Руська, 56 (головний корпус, 1-й поверх)",
        "work": "Пн–Пт: 9:00–18:00  |  Сб: 9:00–14:00",
        "desc": "Головна бібліотека університету. Понад 500 000 примірників. Електронний каталог доступний онлайн.",
        "rooms": [
            "Читальний зал",
            "Абонемент (книги додому)",
            "Медіатека",
            "Електронний каталог: library.tntu.edu.ua",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "sport", "emoji": "🏋️", "cat": "Інфраструктура",
        "name": "Спортивний корпус",
        "address": "вул. Руська, 56 (подвір'я університету)",
        "work": "Пн–Пт: 8:00–21:00  |  Сб: 9:00–16:00",
        "desc": "Спортивний зал та тренажерний зал для студентів. Секції волейболу, баскетболу та інших видів спорту.",
        "rooms": [
            "Великий спортивний зал",
            "Тренажерний зал",
            "Зал для боротьби",
            "Реєстрація: кафедра фізвиховання (гол. корпус)",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "canteen", "emoji": "🍽", "cat": "Інфраструктура",
        "name": "Їдальня та буфет",
        "address": "вул. Руська, 56 (головний корпус, цокольний поверх)",
        "work": "Пн–Пт: 8:30–15:30",
        "desc": "Студентська їдальня з комплексними обідами та буфет з виробами власного виробництва. Знижки для студентів.",
        "rooms": [
            "Їдальня — цокольний поверх",
            "Буфет — 1-й поверх (біля входу)",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "admin", "emoji": "🏢", "cat": "Інфраструктура",
        "name": "Адміністративний корпус",
        "address": "вул. Руська, 56 (правий флігель)",
        "work": "Пн–Пт: 9:00–17:00  |  Обід: 12:30–13:30",
        "desc": "Адміністративні служби університету: відділ кадрів, бухгалтерія, навчальний відділ, міжнародний відділ.",
        "rooms": [
            "Відділ кадрів — 1-й поверх",
            "Бухгалтерія — 2-й поверх",
            "Навчальний відділ — 3-й поверх",
            "Міжнародний відділ — 3-й поверх",
        ],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    # ─── Гуртожитки ──────────────────────────────────────────────────────────
    {
        "key": "dorm1", "emoji": "🏠", "cat": "Гуртожиток",
        "name": "Гуртожиток №1",
        "address": "вул. Микулинецька, 46а",
        "work": "Цілодобово (вхід до 23:00 без перепустки)",
        "desc": "Студентський гуртожиток. Для заселення — звернись до деканату або студентської профспілки у серпні.",
        "rooms": [
            "Комендатура — 1-й поверх",
            "Кімнати на 2–3 особи",
            "Кухня на кожному поверсі",
            "Пральня",
        ],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key": "dorm2", "emoji": "🏠", "cat": "Гуртожиток",
        "name": "Гуртожиток №2",
        "address": "вул. Микулинецька, 46б",
        "work": "Цілодобово (вхід до 23:00 без перепустки)",
        "desc": "Другий студентський гуртожиток ТНТУ. Умови та правила аналогічні до гуртожитку №1.",
        "rooms": [
            "Комендатура — 1-й поверх",
            "Кімнати на 2–3 особи",
            "Кухня на кожному поверсі",
            "Кімната відпочинку",
        ],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
]

CATEGORIES = ["Навчальний корпус", "Інфраструктура", "Гуртожиток"]

CAT_EMOJI = {
    "Навчальний корпус": "🏫",
    "Інфраструктура":    "🔧",
    "Гуртожиток":        "🏠",
}


def main_keyboard() -> InlineKeyboardMarkup:
    """Категорії об'єктів."""
    buttons = [
        [InlineKeyboardButton(
            text=f"{CAT_EMOJI[cat]} {cat} ({sum(1 for b in BUILDINGS if b['cat']==cat)})",
            callback_data=f"bcat:{cat}"
        )]
        for cat in CATEGORIES
    ]
    buttons.append([InlineKeyboardButton(
        text="📋 Всі об'єкти одним списком",
        callback_data="bcat:all"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_keyboard(cat: str) -> InlineKeyboardMarkup:
    items = [b for b in BUILDINGS if b["cat"] == cat] if cat != "all" else BUILDINGS
    buttons = [
        [InlineKeyboardButton(
            text=f"{b['emoji']} {b['name']}",
            callback_data=f"bld:{b['key']}"
        )]
        for b in items
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="bld:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def building_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ До списку корпусів", callback_data="bld:menu")]
    ])


def format_building(b: dict) -> str:
    rooms = "\n".join(f"  • {r}" for r in b["rooms"])
    return (
        f"{b['emoji']} {b['name']}\n"
        f"{'─' * 30}\n"
        f"📍 Адреса: {b['address']}\n"
        f"🕐 Режим роботи:\n  {b['work']}\n\n"
        f"{b['desc']}\n\n"
        f"Що тут є:\n{rooms}\n\n"
        f"🗺 Карта: {b['map']}"
    )


def format_all_buildings() -> str:
    lines = ["🏛 Всі об'єкти ТНТУ\n"]
    for cat in CATEGORIES:
        lines.append(f"\n{CAT_EMOJI[cat]} {cat.upper()}")
        for b in BUILDINGS:
            if b["cat"] == cat:
                lines.append(f"{b['emoji']} {b['name']}")
                lines.append(f"   📍 {b['address']}")
                lines.append(f"   🕐 {b['work']}\n")
    return "\n".join(lines)


@router.message(F.text == "🏛 Корпуси ТНТУ")
async def buildings_menu(message: Message):
    await message.answer(
        f"🏛 Корпуси та об'єкти ТНТУ\n\n"
        f"Всього об'єктів: {len(BUILDINGS)}\n\n"
        "Оберіть категорію:",
        reply_markup=main_keyboard()
    )


@router.callback_query(F.data == "bld:menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"🏛 Корпуси та об'єкти ТНТУ\n\nВсього об'єктів: {len(BUILDINGS)}\n\nОберіть категорію:",
        reply_markup=main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bcat:"))
async def category_chosen(callback: CallbackQuery):
    cat = callback.data.split(":", 1)[1]
    if cat == "all":
        text = format_all_buildings()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="bld:menu")]
        ])
        await callback.message.edit_text(text, reply_markup=kb,
                                         disable_web_page_preview=True)
    else:
        count = sum(1 for b in BUILDINGS if b["cat"] == cat)
        await callback.message.edit_text(
            f"{CAT_EMOJI.get(cat, '')} {cat}\n\nОберіть об'єкт ({count}):",
            reply_markup=category_keyboard(cat)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("bld:"))
async def building_info(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    if key == "menu":
        return  # вже оброблено вище

    b = next((x for x in BUILDINGS if x["key"] == key), None)
    if not b:
        await callback.answer("❌ Не знайдено")
        return

    await callback.message.edit_text(
        format_building(b),
        reply_markup=building_keyboard(),
        disable_web_page_preview=True
    )
    await callback.answer()