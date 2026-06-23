from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

BUILDINGS = {
    "main": {
        "name": "Головний корпус",
        "address": "вул. Руська, 56",
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
        "faculties": ["ФІС — поверхи 3-5", "Ректорат", "Бібліотека", "Актова зала"],
        "work": "Пн-Пт: 8:00-20:00, Сб: 8:00-14:00",
        "info": "Центральний корпус університету. Тут знаходиться ректорат, більшість аудиторій ФІС та головна бібліотека.",
        "emoji": "🏛"
    },
    "corpus2": {
        "name": "Корпус №2 (Навчально-лабораторний)",
        "address": "вул. Руська, 56 (за головним корпусом)",
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
        "faculties": ["ФІС — лабораторії", "Комп'ютерні класи", "Лабораторії ФПТ"],
        "work": "Пн-Пт: 8:00-20:00",
        "info": "Тут знаходяться комп'ютерні класи та лабораторії кафедр програмної інженерії і комп'ютерних систем.",
        "emoji": "🖥"
    },
    "corpus3": {
        "name": "Корпус №3 (ФПТ)",
        "address": "вул. Микулинецька, 46",
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
        "faculties": ["ФПТ — всі кафедри", "Радіотехнічні лабораторії", "Електротехнічні лабораторії"],
        "work": "Пн-Пт: 8:00-19:00",
        "info": "Корпус Факультету прикладних інформаційних технологій та електроінженерії.",
        "emoji": "⚡️"
    },
    "corpus4": {
        "name": "Корпус №4 (ФМТ)",
        "address": "вул. Танцорова, 2",
        "map": "https://maps.app.goo.gl/somelink",
        "faculties": ["ФМТ — всі кафедри", "Механічні майстерні", "Лабораторії матеріалів"],
        "work": "Пн-Пт: 8:00-18:00",
        "info": "Корпус Факультету інженерії машин, споруд та технологій.",
        "emoji": "⚙️"
    },
    "corpus5": {
        "name": "Корпус ФЕМ",
        "address": "вул. Білогірська, 50",
        "map": "https://maps.app.goo.gl/somelink2",
        "faculties": ["ФЕМ — всі кафедри", "Аудиторії економічних дисциплін"],
        "work": "Пн-Пт: 8:00-19:00",
        "info": "Корпус Факультету економіки та менеджменту.",
        "emoji": "📊"
    },
    "library": {
        "name": "Наукова бібліотека",
        "address": "вул. Руська, 56 (1-й поверх головного корпусу)",
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
        "faculties": ["Читальний зал", "Абонемент", "Електронний каталог"],
        "work": "Пн-Пт: 9:00-18:00, Сб: 9:00-14:00",
        "info": "Головна бібліотека університету. Можна взяти підручники за читацьким квитком або користуватись читальним залом.",
        "emoji": "📚"
    },
    "sport": {
        "name": "Спортивний корпус",
        "address": "вул. Руська, 56 (подвір'я)",
        "map": "https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
        "faculties": ["Спортивний зал", "Тренажерний зал", "Волейбол", "Баскетбол"],
        "work": "Пн-Пт: 8:00-21:00, Сб: 9:00-16:00",
        "info": "Спортивний корпус для студентів. Запис через кафедру фізичного виховання.",
        "emoji": "🏋️"
    },
    "dormitory": {
        "name": "Гуртожитки",
        "address": "вул. Микулинецька, 46а та 46б",
        "map": "https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
        "faculties": ["Гуртожиток №1", "Гуртожиток №2", "Комендатура"],
        "work": "Цілодобово",
        "info": "Студентські гуртожитки ТНТУ. Для заселення — звертатись до деканату або студентської профспілки.",
        "emoji": "🏠"
    },
}


def buildings_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🏛 Головний корпус", callback_data="bld:main"),
            InlineKeyboardButton(text="🖥 Корпус №2", callback_data="bld:corpus2"),
        ],
        [
            InlineKeyboardButton(text="⚡️ Корпус №3 (ФПТ)", callback_data="bld:corpus3"),
            InlineKeyboardButton(text="⚙️ Корпус №4 (ФМТ)", callback_data="bld:corpus4"),
        ],
        [
            InlineKeyboardButton(text="📊 Корпус ФЕМ", callback_data="bld:corpus5"),
            InlineKeyboardButton(text="📚 Бібліотека", callback_data="bld:library"),
        ],
        [
            InlineKeyboardButton(text="🏋️ Спорткорпус", callback_data="bld:sport"),
            InlineKeyboardButton(text="🏠 Гуртожитки", callback_data="bld:dormitory"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_building(b: dict) -> str:
    lines = [
        f"{b['emoji']} {b['name']}\n",
        f"📍 Адреса: {b['address']}",
        f"🕐 Режим роботи: {b['work']}",
        f"\n{b['info']}\n",
        f"Що тут є:",
    ]
    for item in b["faculties"]:
        lines.append(f"  • {item}")
    lines.append(f"\n🗺 Карта: {b['map']}")
    return "\n".join(lines)


@router.message(F.text == "🏛 Корпуси ТНТУ")
async def buildings_menu(message: Message):
    await message.answer(
        "🏛 Корпуси та об'єкти ТНТУ\n\n"
        "Оберіть корпус щоб дізнатись адресу, розташування і що там знаходиться:",
        reply_markup=buildings_keyboard()
    )


@router.callback_query(F.data.startswith("bld:"))
async def building_info(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    building = BUILDINGS.get(key)

    if not building:
        await callback.answer("❌ Не знайдено")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ До всіх корпусів", callback_data="bld:back")]
    ])

    await callback.message.edit_text(
        format_building(building),
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data == "bld:back")
async def buildings_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏛 Корпуси та об'єкти ТНТУ\n\nОберіть корпус:",
        reply_markup=buildings_keyboard()
    )
    await callback.answer()