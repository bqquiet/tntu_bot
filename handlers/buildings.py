from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

BUILDINGS = [
    {
        "key": "main",
        "emoji": "🏛",
        "name": "Головний корпус (№1)",
        "address": "вул. Руська, 56",
        "work": "Пн–Пт: 8:00–20:00 | Сб: 8:00–14:00",
        "desc": "Центральний корпус університету. Тут ректорат, деканати, більшість аудиторій ФІС, актова зала і головна бібліотека.",
        "rooms": ["Ректорат — 1-й пов.", "Деканат ФІС — к.7, 1-й пов.", "Бібліотека — 1-й пов.", "Актова зала — 2-й пов."],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "corp2",
        "emoji": "🖥",
        "name": "Навчально-лабораторний корпус (№2)",
        "address": "вул. Руська, 56 (за головним)",
        "work": "Пн–Пт: 8:00–20:00",
        "desc": "Комп'ютерні класи та лабораторії кафедр програмної інженерії, комп'ютерних систем і мереж.",
        "rooms": ["Комп'ютерні класи — 3–5 пов.", "Лабораторія ПІ — ауд. 401-407", "Лабораторія КС — ауд. 201-205"],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "corp3",
        "emoji": "⚡️",
        "name": "Корпус №3 (ФПТ)",
        "address": "вул. Микулинецька, 46",
        "work": "Пн–Пт: 8:00–19:00",
        "desc": "Корпус факультету ФПТ. Кафедри електричної інженерії, радіотехніки, КТ та приладів.",
        "rooms": ["Деканат ФПТ — 1-й пов.", "Радіотехнічні лабораторії", "Електролабораторії", "Кафедра КТ"],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key": "corp4",
        "emoji": "⚙️",
        "name": "Корпус №4 (ФМТ)",
        "address": "вул. Танцорова, 2",
        "work": "Пн–Пт: 8:00–18:00",
        "desc": "Корпус факультету ФМТ. Механічні майстерні, лабораторії матеріалів і машинобудування.",
        "rooms": ["Деканат ФМТ — 1-й пов.", "Механічні майстерні", "Лабораторія ТМІ", "Кафедра ВІ"],
        "map": "https://maps.app.goo.gl/somelink1",
    },
    {
        "key": "corp5",
        "emoji": "📊",
        "name": "Корпус №5 (ФЕМ)",
        "address": "вул. Білогірська, 50",
        "work": "Пн–Пт: 8:00–18:00",
        "desc": "Корпус факультету ФЕМ. Кафедри менеджменту, маркетингу, обліку та економіки.",
        "rooms": ["Деканат ФЕМ — 1-й пов.", "Аудиторії кафедр ФЕМ"],
        "map": "https://maps.app.goo.gl/somelink2",
    },
    {
        "key": "library",
        "emoji": "📚",
        "name": "Наукова бібліотека",
        "address": "вул. Руська, 56 (головний корпус, 1-й пов.)",
        "work": "Пн–Пт: 9:00–18:00 | Сб: 9:00–14:00",
        "desc": "Головна бібліотека університету. Понад 500 000 примірників книг. Для запису — студентський квиток.",
        "rooms": ["Читальний зал", "Абонемент", "Медіатека", "Електронний каталог"],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "sport",
        "emoji": "🏋️",
        "name": "Спортивний корпус",
        "address": "вул. Руська, 56 (подвір'я)",
        "work": "Пн–Пт: 8:00–21:00 | Сб: 9:00–16:00",
        "desc": "Спортивний зал, тренажерний зал, зал для ігрових видів спорту. Запис через кафедру фізвиховання.",
        "rooms": ["Спортивний зал", "Тренажерний зал", "Волейбол / Баскетбол"],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "dorm1",
        "emoji": "🏠",
        "name": "Гуртожиток №1",
        "address": "вул. Микулинецька, 46а",
        "work": "Цілодобово",
        "desc": "Студентський гуртожиток ТНТУ. Для заселення звертатись до деканату або профспілки на початку серпня.",
        "rooms": ["Комендатура — 1-й пов.", "Кімнати на 2–3 особи", "Кухня на кожному поверсі"],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key": "dorm2",
        "emoji": "🏠",
        "name": "Гуртожиток №2",
        "address": "вул. Микулинецька, 46б",
        "work": "Цілодобово",
        "desc": "Другий студентський гуртожиток ТНТУ. Умови аналогічні до гуртожитку №1.",
        "rooms": ["Комендатура — 1-й пов.", "Кімнати на 2–3 особи", "Спільні кімнати відпочинку"],
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key": "canteen",
        "emoji": "🍽",
        "name": "Їдальня / Буфет",
        "address": "вул. Руська, 56 (головний корпус, цокольний поверх)",
        "work": "Пн–Пт: 8:30–15:30",
        "desc": "Студентська їдальня в головному корпусі. Комплексні обіди, буфет, кава. Знижки для студентів.",
        "rooms": ["Їдальня — цокольний пов.", "Буфет — 1-й пов."],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key": "admin",
        "emoji": "🏢",
        "name": "Адміністративний корпус",
        "address": "вул. Руська, 56",
        "work": "Пн–Пт: 9:00–17:00",
        "desc": "Тут знаходяться відділ кадрів, бухгалтерія, планово-фінансовий відділ та інші адміністративні служби.",
        "rooms": ["Відділ кадрів", "Бухгалтерія", "Навчальний відділ", "Міжнародний відділ"],
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
]


def buildings_menu_keyboard() -> InlineKeyboardMarkup:
    rows = []
    # По 2 кнопки в рядку
    for i in range(0, len(BUILDINGS), 2):
        row = []
        for b in BUILDINGS[i:i+2]:
            row.append(InlineKeyboardButton(
                text=f"{b['emoji']} {b['name'][:22]}",
                callback_data=f"bld:{b['key']}"
            ))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Всі корпуси", callback_data="bld:menu")]
    ])


def format_building(b: dict) -> str:
    lines = [
        f"{b['emoji']} {b['name']}",
        f"",
        f"📍 {b['address']}",
        f"🕐 {b['work']}",
        f"",
        f"{b['desc']}",
        f"",
        "Що тут є:",
    ]
    for r in b["rooms"]:
        lines.append(f"  • {r}")
    lines.append(f"")
    lines.append(f"🗺 Карта: {b['map']}")
    return "\n".join(lines)


@router.message(F.text == "🏛 Корпуси ТНТУ")
async def buildings_menu(message: Message):
    await message.answer(
        f"🏛 Корпуси та об'єкти ТНТУ\n\n"
        f"Всього об'єктів: {len(BUILDINGS)}\n\n"
        "Обери корпус для детальної інформації:",
        reply_markup=buildings_menu_keyboard()
    )


@router.callback_query(F.data == "bld:menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"🏛 Корпуси та об'єкти ТНТУ\n\nВсього об'єктів: {len(BUILDINGS)}\n\nОбери корпус:",
        reply_markup=buildings_menu_keyboard()
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
        reply_markup=back_keyboard()
    )
    await callback.answer()