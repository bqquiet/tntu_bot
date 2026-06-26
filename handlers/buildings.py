from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Офіційне джерело адрес: tntu.edu.ua/?p=uk/about/building-locations
BUILDINGS = [
    # ─── 11 навчальних корпусів ───────────────────────────────────────────────
    {
        "key":"c1","cat":"corp","emoji":"🏛","num":"№1",
        "name":"Корпус №1 (Головний)",
        "address":"вул. Руська, 56",
        "work":"Пн–Пт 8:00–20:00  |  Сб 8:00–14:00",
        "desc":"Головний корпус університету. Ректорат, деканат ФІС, більшість аудиторій ФІС, актова зала, бібліотека.",
        "rooms":["Ректорат — к.107, 1-й пов.","Деканат ФІС — к.607, 6-й пов.","Бібліотека — 1-й пов.","Кафедри ФІС — 3–7 поверхи"],
        "map":"https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key":"c2","cat":"corp","emoji":"🖥","num":"№2",
        "name":"Корпус №2 (Навчально-лабораторний)",
        "address":"вул. Руська, 56",
        "work":"Пн–Пт 8:00–20:00",
        "desc":"Комп'ютерні класи та лабораторії ФІС. Тут кафедри фізики, автоматизації та їхні лаборатории.",
        "rooms":["Кафедра фізики — к.40","Лабораторія автоматизації — ауд. 8, 9, 11","Комп'ютерні класи — 3–5 поверхи"],
        "map":"https://maps.app.goo.gl/Yb2q8kFZQxvp3NZMA",
    },
    {
        "key":"c3","cat":"corp","emoji":"🏫","num":"№3",
        "name":"Корпус №3",
        "address":"вул. Федьковича, 9",
        "work":"Пн–Пт 8:00–19:00",
        "desc":"Навчальний корпус університету.",
        "rooms":["Аудиторії для лекцій та практик"],
        "map":"https://maps.app.goo.gl/somelink3",
    },
    {
        "key":"c4","cat":"corp","emoji":"🏫","num":"№4",
        "name":"Корпус №4",
        "address":"вул. Руська, 56А",
        "work":"Пн–Пт 8:00–19:00",
        "desc":"Навчальний корпус університету. Розташований поруч з головним корпусом.",
        "rooms":["Аудиторії та лабораторії"],
        "map":"https://maps.app.goo.gl/somelink4",
    },
    {
        "key":"c5","cat":"corp","emoji":"🏫","num":"№5",
        "name":"Корпус №5",
        "address":"вул. Старий Поділ, 2",
        "work":"Пн–Пт 8:00–18:00",
        "desc":"Навчальний корпус університету.",
        "rooms":["Аудиторії та лабораторії"],
        "map":"https://maps.app.goo.gl/somelink5",
    },
    {
        "key":"c6","cat":"corp","emoji":"🏫","num":"№6",
        "name":"Корпус №6",
        "address":"вул. Гоголя, 6",
        "work":"Пн–Пт 8:00–18:00",
        "desc":"Навчальний корпус університету.",
        "rooms":["Аудиторії та лабораторії"],
        "map":"https://maps.app.goo.gl/somelink6",
    },
    {
        "key":"c7","cat":"corp","emoji":"⚙️","num":"№7",
        "name":"Корпус №7 «Ватра»",
        "address":"вул. Микулинецька, 46",
        "work":"Пн–Пт 8:00–19:00",
        "desc":"Корпус ФПТ та ФМТ. Лабораторії електроінженерії, радіотехніки, механічні майстерні.",
        "rooms":["Деканат ФПТ","Радіотехнічні лабораторії","Електролабораторії","Механічні майстерні ФМТ"],
        "map":"https://maps.app.goo.gl/4nXBqhNJmwvNGsB3A",
    },
    {
        "key":"c8","cat":"corp","emoji":"🏢","num":"№8",
        "name":"Корпус №8",
        "address":"вул. Гоголя, 8",
        "work":"Пн–Пт 8:00–18:00",
        "desc":"Адміністративний корпус. Тут навчальний відділ, підготовчі курси, студентське містечко.",
        "rooms":["Навчальний відділ — к.20","Підготовчі курси — к.20","Адміністрація студмістечка — ауд. 21а"],
        "map":"https://maps.app.goo.gl/somelink8",
    },
    {
        "key":"c9","cat":"corp","emoji":"🔬","num":"№9",
        "name":"Корпус №9 «Сатурн»",
        "address":"вул. Текстильна, 28",
        "work":"Пн–Пт 8:00–18:00",
        "desc":"Навчальний корпус університету. Лабораторії та аудиторії.",
        "rooms":["Аудиторії та лабораторії"],
        "map":"https://maps.app.goo.gl/somelink9",
    },
    {
        "key":"c10","cat":"corp","emoji":"🎭","num":"№10",
        "name":"Корпус №10 «Політехнік»",
        "address":"вул. Білогірська, 50",
        "work":"Пн–Пт 8:00–20:00",
        "desc":"Спортивно-мистецький комплекс та корпус ФЕМ. Тут актова зала, басейн, спортзали, кафедри економічних дисциплін.",
        "rooms":["Деканат ФЕМ","Кафедра маркетингу (МК) — к.209","Актова зала","Плавальний басейн","Спортивні зали"],
        "map":"https://maps.app.goo.gl/somelink10",
    },
    {
        "key":"c11","cat":"corp","emoji":"🏭","num":"№11",
        "name":"Корпус №11 «Комбайновий завод»",
        "address":"вул. Лук'яновича, 8",
        "work":"Пн–Пт 8:00–18:00",
        "desc":"Навчально-виробничий корпус університету. Технічні лабораторії та майстерні.",
        "rooms":["Технічні лабораторії","Навчально-виробничі майстерні"],
        "map":"https://maps.app.goo.gl/somelink11",
    },
    # ─── 3 гуртожитки ────────────────────────────────────────────────────────
    {
        "key":"d1","cat":"dorm","emoji":"🏠","num":"№1",
        "name":"Гуртожиток №1",
        "address":"вул. Шептицького, 13",
        "work":"Цілодобово",
        "desc":"Студентський гуртожиток ТНТУ. 555 місць. Зал для самопідготовки, спортивний майданчик.",
        "rooms":["Комендатура — 1-й пов.","Зал самопідготовки","Спортивний майданчик","Тел.: 0352 25-35-96"],
        "map":"https://maps.app.goo.gl/somelink_d1",
    },
    {
        "key":"d2","cat":"dorm","emoji":"🏠","num":"№2",
        "name":"Гуртожиток №2",
        "address":"вул. Замонастирська, 18",
        "work":"Цілодобово",
        "desc":"Студентський гуртожиток ТНТУ. 274 місця. П'ятиповерхова будівля коридорного типу.",
        "rooms":["Комендатура — 1-й пов.","Кімната самопідготовки","Спортивний майданчик","Тел.: 0352 52-44-86"],
        "map":"https://maps.app.goo.gl/somelink_d2",
    },
    {
        "key":"d3","cat":"dorm","emoji":"🏠","num":"№3",
        "name":"Гуртожиток №3",
        "address":"вул. Тарнавського, 7а",
        "work":"Цілодобово",
        "desc":"Студентський гуртожиток ТНТУ. Кухні з електроплитами на кожному поверсі, медпункт.",
        "rooms":["Комендатура — 1-й пов.","Медичний пункт","Кухні на кожному поверсі","Душові — 1-й пов."],
        "map":"https://maps.app.goo.gl/somelink_d3",
    },
]

CATS = {"corp": ("🏫", "Навчальні корпуси"), "dorm": ("🏠", "Гуртожитки")}


def main_kb() -> InlineKeyboardMarkup:
    corp_count = sum(1 for b in BUILDINGS if b["cat"] == "corp")
    dorm_count = sum(1 for b in BUILDINGS if b["cat"] == "dorm")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🏫 Навчальні корпуси ({corp_count})",
            callback_data="bcat:corp"
        )],
        [InlineKeyboardButton(
            text=f"🏠 Гуртожитки ({dorm_count})",
            callback_data="bcat:dorm"
        )],
        [InlineKeyboardButton(
            text="📋 Всі об'єкти списком",
            callback_data="bcat:all"
        )],
    ])


def category_kb(cat: str) -> InlineKeyboardMarkup:
    items = [b for b in BUILDINGS if b["cat"] == cat]
    buttons = [
        [InlineKeyboardButton(
            text=f"{b['emoji']} Корпус {b['num']}" if cat == "corp" else f"{b['emoji']} {b['name']}",
            callback_data=f"bld:{b['key']}"
        )]
        for b in items
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="bld:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ До списку", callback_data="bld:menu")]
    ])


def fmt(b: dict) -> str:
    rooms = "\n".join(f"  • {r}" for r in b["rooms"])
    return (
        f"{b['emoji']} {b['name']}\n"
        f"{'─'*32}\n"
        f"📍 {b['address']}\n"
        f"🕐 {b['work']}\n\n"
        f"{b['desc']}\n\n"
        f"Що тут є:\n{rooms}\n\n"
        f"🗺 Карта: {b['map']}"
    )


def fmt_all() -> str:
    lines = ["🏛 Всі об'єкти ТНТУ\n"]
    for cat, (emoji, label) in CATS.items():
        lines.append(f"\n{emoji} {label.upper()}")
        lines.append("─" * 28)
        for b in BUILDINGS:
            if b["cat"] == cat:
                lines.append(f"{b['emoji']} {b['name']}")
                lines.append(f"   📍 {b['address']}")
    lines.append(f"\n🔗 Офіційна сторінка:\nhttps://tntu.edu.ua/?p=uk/about/building-locations")
    return "\n".join(lines)


@router.message(F.text == "🏛 Корпуси ТНТУ")
async def buildings_menu(message: Message):
    corp = sum(1 for b in BUILDINGS if b["cat"] == "corp")
    dorm = sum(1 for b in BUILDINGS if b["cat"] == "dorm")
    await message.answer(
        f"🏛 Корпуси та гуртожитки ТНТУ\n\n"
        f"Навчальних корпусів: {corp}\n"
        f"Гуртожитків: {dorm}\n\n"
        "Оберіть категорію:",
        reply_markup=main_kb()
    )


@router.callback_query(F.data == "bld:menu")
async def back_to_menu(callback: CallbackQuery):
    corp = sum(1 for b in BUILDINGS if b["cat"] == "corp")
    dorm = sum(1 for b in BUILDINGS if b["cat"] == "dorm")
    await callback.message.edit_text(
        f"🏛 Корпуси та гуртожитки ТНТУ\n\nНавчальних корпусів: {corp}\nГуртожитків: {dorm}\n\nОберіть категорію:",
        reply_markup=main_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bcat:"))
async def cat_chosen(callback: CallbackQuery):
    cat = callback.data.split(":", 1)[1]
    if cat == "all":
        await callback.message.edit_text(
            fmt_all(),
            reply_markup=back_kb(),
            disable_web_page_preview=True
        )
    else:
        emoji, label = CATS.get(cat, ("", cat))
        count = sum(1 for b in BUILDINGS if b["cat"] == cat)
        await callback.message.edit_text(
            f"{emoji} {label} ({count})\n\nОберіть об'єкт:",
            reply_markup=category_kb(cat)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("bld:"))
async def building_info(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    if key == "menu":
        return
    b = next((x for x in BUILDINGS if x["key"] == key), None)
    if not b:
        await callback.answer("❌ Не знайдено")
        return
    await callback.message.edit_text(
        fmt(b), reply_markup=back_kb(), disable_web_page_preview=True
    )
    await callback.answer()