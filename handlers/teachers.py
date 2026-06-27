import json
import os
import urllib.parse
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE   = "data/teachers.json"
FACULTIES = ["ФІС", "ФПТ", "ФМТ", "ФЕМ"]
FAC_EMOJI = {"ФІС":"💻", "ФПТ":"⚡️", "ФМТ":"⚙️", "ФЕМ":"📊"}
TNTU = "https://tntu.edu.ua"


class TS(StatesGroup):
    search = State()


# ── Дані ─────────────────────────────────────────────────────────────────────

def load() -> list[dict]:
    if not os.path.exists(FILE):
        return []
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)


def by_faculty(fac: str) -> list[dict]:
    return [t for t in load() if t.get("faculty") == fac]


def by_dept(fac: str, dept: str) -> list[dict]:
    return [t for t in load()
            if t.get("faculty") == fac and t.get("department") == dept]


def get_depts(fac: str) -> list[str]:
    return sorted(set(t["department"] for t in load() if t.get("faculty") == fac))


def find(query: str, fac: str = "") -> list[dict]:
    q = query.lower()
    return [
        t for t in load()
        if (not fac or t.get("faculty") == fac)
        and q in " ".join([
            t.get("name",""), t.get("position",""),
            t.get("department",""), *t.get("courses",[])
        ]).lower()
    ]


# ── Форматування картки викладача ─────────────────────────────────────────────

def teacher_card(t: dict) -> str:
    lines = [f"👨‍🏫 <b>{t['name']}</b>"]
    if t.get("position"):
        lines.append(f"📌 <i>{t['position']}</i>")
    fac   = t.get("faculty","")
    dept  = t.get("department","")
    lines.append(f"🏛 {dept}" + (f" · <b>{fac}</b>" if fac else ""))
    if t.get("email"):
        lines.append(f"📧 <a href=\"mailto:{t['email']}\">{t['email']}</a>")
    if t.get("courses"):
        lines.append(f"📚 {', '.join(t['courses'])}")
    if t.get("consultation"):
        lines.append(f"🕐 <i>Консультації: {t['consultation']}</i>")
    return "\n".join(lines)


def teacher_kb(t: dict) -> InlineKeyboardMarkup:
    buttons = []
    if t.get("schedule_url"):
        buttons.append([InlineKeyboardButton(
            text="📅 Розклад викладача",
            url=t["schedule_url"]
        )])
    name_encoded = urllib.parse.quote(t.get("name",""))
    buttons.append([InlineKeyboardButton(
        text="🔍 Знайти в Google",
        url=f"https://www.google.com/search?q={name_encoded}+ТНТУ"
    )])
    buttons.append([InlineKeyboardButton(
        text="◀️ До списку",
        callback_data=f"t_back:{t.get('faculty','')}:{t.get('department','')}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Клавіатури ────────────────────────────────────────────────────────────────

def fac_kb() -> InlineKeyboardMarkup:
    total = len(load())
    buttons = [
        [InlineKeyboardButton(
            text=f"{FAC_EMOJI.get(f,'')} {f}  ({sum(1 for t in load() if t.get('faculty')==f)})",
            callback_data=f"t_fac:{f}"
        )]
        for f in FACULTIES
    ]
    buttons.append([InlineKeyboardButton(
        text="🔍 Пошук по всьому університету",
        callback_data="t_search:all"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dept_kb(fac: str) -> InlineKeyboardMarkup:
    depts = get_depts(fac)
    buttons = []
    for d in depts:
        count = len(by_dept(fac, d))
        # Скорочена назва для кнопки
        short = d.replace("Кафедра ","").strip()
        if len(short) > 38: short = short[:36] + "…"
        buttons.append([InlineKeyboardButton(
            text=f"{short} ({count})",
            callback_data=f"t_dept:{fac}:{d[:60]}"
        )])
    buttons.append([InlineKeyboardButton(
        text="🔍 Пошук по факультету",
        callback_data=f"t_search:{fac}"
    )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="t_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def teachers_list_kb(teachers: list[dict], page: int = 0, per: int = 10,
                     fac: str = "", dept: str = "") -> InlineKeyboardMarkup:
    """Нумерований список викладачів — по 10 на сторінці."""
    total  = len(teachers)
    start  = page * per
    chunk  = teachers[start:start + per]
    buttons = []

    for i, t in enumerate(chunk):
        num  = start + i + 1
        name = t["name"]
        # Скорочуємо до "Прізвище І.П."
        parts = name.split()
        if len(parts) >= 3:
            short = f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
        elif len(parts) == 2:
            short = f"{parts[0]} {parts[1][0]}."
        else:
            short = name[:30]
        buttons.append([InlineKeyboardButton(
            text=f"{num}. {short}",
            callback_data=f"t_card:{fac}:{dept[:50]}:{start+i}"
        )])

    # Навігація
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"t_page:{fac}:{dept[:50]}:{page-1}"))
    if start + per < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"t_page:{fac}:{dept[:50]}:{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="◀️ До кафедр", callback_data=f"t_fac:{fac}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлери ──────────────────────────────────────────────────────────────────

@router.message(F.text == "👨‍🏫 Викладачі")
async def teachers_menu(message: Message, state: FSMContext):
    await state.clear()
    total = len(load())
    await message.answer(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\n"
        f"В базі: <b>{total}</b> викладачів з усіх факультетів\n\n"
        f"Оберіть факультет:",
        parse_mode="HTML",
        reply_markup=fac_kb()
    )


@router.callback_query(F.data == "t_main")
async def back_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    total = len(load())
    await cb.message.edit_text(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\nВ базі: <b>{total}</b> викладачів\n\nОберіть факультет:",
        parse_mode="HTML", reply_markup=fac_kb()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_fac:"))
async def fac_chosen(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    fac   = cb.data.split(":", 1)[1]
    emoji = FAC_EMOJI.get(fac, "")
    count = len(by_faculty(fac))
    depts = get_depts(fac)
    await cb.message.edit_text(
        f"{emoji} <b>{fac}</b> — {count} викладачів\n"
        f"Кафедр: {len(depts)}\n\n"
        f"Оберіть кафедру:",
        parse_mode="HTML",
        reply_markup=dept_kb(fac)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_dept:"))
async def dept_chosen(cb: CallbackQuery, state: FSMContext):
    _, fac, dept = cb.data.split(":", 2)
    teachers = by_dept(fac, dept)

    if not teachers:
        await cb.answer("Викладачів не знайдено")
        return

    # Сортуємо за прізвищем
    teachers.sort(key=lambda t: t["name"])

    text = (
        f"🏛 <b>{dept}</b>\n"
        f"Факультет: <b>{fac}</b>\n"
        f"Викладачів: <b>{len(teachers)}</b>\n\n"
        f"<i>Оберіть викладача зі списку:</i>"
    )
    await cb.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=teachers_list_kb(teachers, page=0, fac=fac, dept=dept)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_page:"))
async def turn_page(cb: CallbackQuery):
    _, fac, dept, page_s = cb.data.split(":", 3)
    page     = int(page_s)
    teachers = by_dept(fac, dept)
    teachers.sort(key=lambda t: t["name"])

    text = (
        f"🏛 <b>{dept}</b>\n"
        f"Викладачів: <b>{len(teachers)}</b>\n\n"
        f"<i>Сторінка {page+1}</i>"
    )
    await cb.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=teachers_list_kb(teachers, page=page, fac=fac, dept=dept)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_card:"))
async def teacher_card_cb(cb: CallbackQuery):
    _, fac, dept, idx_s = cb.data.split(":", 3)
    idx      = int(idx_s)
    teachers = by_dept(fac, dept)
    teachers.sort(key=lambda t: t["name"])

    if idx >= len(teachers):
        await cb.answer("❌ Не знайдено")
        return

    t = teachers[idx]
    await cb.message.edit_text(
        teacher_card(t),
        parse_mode="HTML",
        reply_markup=teacher_kb(t),
        disable_web_page_preview=True
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_back:"))
async def back_to_list(cb: CallbackQuery):
    _, fac, dept = cb.data.split(":", 2)
    teachers = by_dept(fac, dept)
    teachers.sort(key=lambda t: t["name"])

    text = (
        f"🏛 <b>{dept}</b>\n"
        f"Факультет: <b>{fac}</b>\n"
        f"Викладачів: <b>{len(teachers)}</b>\n\n"
        f"<i>Оберіть викладача:</i>"
    )
    await cb.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=teachers_list_kb(teachers, page=0, fac=fac, dept=dept)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_search:"))
async def search_start(cb: CallbackQuery, state: FSMContext):
    fac = cb.data.split(":", 1)[1]
    await state.update_data(fac=fac if fac != "all" else "")
    await state.set_state(TS.search)
    scope = f"факультету <b>{fac}</b>" if fac != "all" else "всього університету"
    await cb.message.edit_text(
        f"🔍 Пошук по {scope}\n\nВведи прізвище, ім'я або назву дисципліни:",
        parse_mode="HTML"
    )
    await cb.answer()


@router.message(TS.search)
async def do_search(message: Message, state: FSMContext):
    data  = await state.get_data()
    fac   = data.get("fac", "")
    await state.clear()
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❌ Запит занадто короткий.")
        return

    results = find(query, fac)
    if not results:
        await message.answer(
            f"🔍 За запитом <b>{query}</b> нічого не знайдено.\n\n"
            f"Спробуй інше прізвище або дисципліну.",
            parse_mode="HTML", reply_markup=fac_kb()
        )
        return

    results.sort(key=lambda t: t["name"])
    total = len(results)
    await message.answer(
        f"🔍 Знайдено: <b>{total}</b> результатів за запитом «{query}»",
        parse_mode="HTML"
    )
    for t in results[:8]:
        await message.answer(
            teacher_card(t),
            parse_mode="HTML",
            reply_markup=teacher_kb(t),
            disable_web_page_preview=True
        )
    if total > 8:
        await message.answer(
            f"<i>...і ще {total-8}. Уточни запит для точнішого результату.</i>",
            parse_mode="HTML"
        )