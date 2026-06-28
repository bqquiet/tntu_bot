"""
Навігація: Факультет → Кафедра (індекс) → Список викладачів → Картка
Callback_data тримається < 64 байт за рахунок числових індексів.
"""
import json
import os
import urllib.parse
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router   = Router()
FILE     = "data/teachers.json"
FACULTIES = ["ФІС", "ФПТ", "ФМТ", "ФЕМ"]
FAC_EMOJI = {"ФІС":"💻","ФПТ":"⚡️","ФМТ":"⚙️","ФЕМ":"📊"}
TNTU      = "https://tntu.edu.ua"
PER_PAGE  = 10


class TS(StatesGroup):
    search = State()


# ── Дані ─────────────────────────────────────────────────────────────────────

def load() -> list[dict]:
    if not os.path.exists(FILE): return []
    with open(FILE, encoding="utf-8") as f: return json.load(f)

def teachers_of_fac(fac: str) -> list[dict]:
    return sorted([t for t in load() if t.get("faculty") == fac],
                  key=lambda t: t["name"])

def depts_of_fac(fac: str) -> list[str]:
    return sorted(set(t["department"] for t in load() if t.get("faculty") == fac))

def teachers_of_dept(fac: str, di: int) -> list[dict]:
    depts = depts_of_fac(fac)
    if di >= len(depts): return []
    dept = depts[di]
    return sorted([t for t in load()
                   if t.get("faculty")==fac and t.get("department")==dept],
                  key=lambda t: t["name"])

def find_teachers(query: str, fac: str = "") -> list[dict]:
    q = query.lower()
    return sorted([
        t for t in load()
        if (not fac or t.get("faculty")==fac)
        and q in " ".join([t.get("name",""), t.get("position",""),
                           t.get("department",""), *t.get("courses",[])]).lower()
    ], key=lambda t: t["name"])


# ── Форматування ──────────────────────────────────────────────────────────────

def short_name(name: str) -> str:
    parts = name.split()
    if len(parts) >= 3:
        return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
    if len(parts) == 2:
        return f"{parts[0]} {parts[1][0]}."
    return name[:28]


def teacher_card(t: dict) -> str:
    lines = [f"👨‍🏫 <b>{t['name']}</b>"]
    if t.get("position"):
        lines.append(f"📌 <i>{t['position']}</i>")
    lines.append(f"🏛 {t.get('department','')} · <b>{t.get('faculty','')}</b>")
    if t.get("email"):
        lines.append(f"📧 <a href=\"mailto:{t['email']}\">{t['email']}</a>")
    if t.get("courses"):
        lines.append(f"📚 {', '.join(t['courses'])}")
    if t.get("consultation"):
        lines.append(f"🕐 <i>{t['consultation']}</i>")
    return "\n".join(lines)


def teacher_action_kb(t: dict, fac: str, di: int, ti: int) -> InlineKeyboardMarkup:
    """Кнопки під карткою викладача."""
    buttons = []
    if t.get("schedule_url"):
        buttons.append([InlineKeyboardButton(
            text="📅 Розклад на сайті ТНТУ", url=t["schedule_url"]
        )])
    enc = urllib.parse.quote(f"{t.get('name','')} ТНТУ")
    buttons.append([InlineKeyboardButton(
        text="🔍 Пошук у Google",
        url=f"https://www.google.com/search?q={enc}"
    )])
    # Повернення до списку — лише числа, без тексту кафедри!
    buttons.append([InlineKeyboardButton(
        text="◀️ До списку",
        callback_data=f"tl:{fac}:{di}:0"   # fac, dept_idx, page=0
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Клавіатури ────────────────────────────────────────────────────────────────

def fac_kb() -> InlineKeyboardMarkup:
    all_t = load()
    buttons = [
        [InlineKeyboardButton(
            text=f"{FAC_EMOJI.get(f,'')} {f} ({sum(1 for t in all_t if t.get('faculty')==f)})",
            callback_data=f"tf:{f}"
        )]
        for f in FACULTIES
    ]
    buttons.append([InlineKeyboardButton(
        text="🔍 Пошук по університету", callback_data="t_s:all"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dept_kb(fac: str) -> InlineKeyboardMarkup:
    depts = depts_of_fac(fac)
    buttons = []
    for i, d in enumerate(depts):
        cnt   = len(teachers_of_dept(fac, i))
        short = d.replace("Кафедра ","")
        if len(short) > 36: short = short[:34]+"…"
        buttons.append([InlineKeyboardButton(
            text=f"{short} ({cnt})",
            callback_data=f"td:{fac}:{i}"      # ← тільки індекс!
        )])
    buttons.append([InlineKeyboardButton(
        text=f"🔍 Пошук по {fac}", callback_data=f"t_s:{fac}"
    )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="t_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def list_kb(fac: str, di: int, teachers: list[dict],
            page: int = 0) -> InlineKeyboardMarkup:
    total   = len(teachers)
    start   = page * PER_PAGE
    chunk   = teachers[start:start+PER_PAGE]
    buttons = []
    for i, t in enumerate(chunk):
        buttons.append([InlineKeyboardButton(
            text=f"{start+i+1}. {short_name(t['name'])}",
            callback_data=f"tc:{fac}:{di}:{start+i}"   # global teacher index
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"tl:{fac}:{di}:{page-1}"))
    if start + PER_PAGE < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"tl:{fac}:{di}:{page+1}"))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ До кафедр", callback_data=f"tf:{fac}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлери ──────────────────────────────────────────────────────────────────

@router.message(F.text == "👨‍🏫 Викладачі")
async def teachers_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\n"
        f"В базі: <b>{len(load())}</b> викладачів\n\nОберіть факультет:",
        parse_mode="HTML", reply_markup=fac_kb()
    )


@router.callback_query(F.data == "t_main")
async def back_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\nВ базі: <b>{len(load())}</b>\n\nОберіть факультет:",
        parse_mode="HTML", reply_markup=fac_kb()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tf:"))
async def fac_chosen(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    fac   = cb.data.split(":",1)[1]
    depts = depts_of_fac(fac)
    count = len(teachers_of_fac(fac))
    await cb.message.edit_text(
        f"{FAC_EMOJI.get(fac,'')} <b>{fac}</b>\n"
        f"Викладачів: <b>{count}</b>  |  Кафедр: <b>{len(depts)}</b>\n\n"
        f"Оберіть кафедру:",
        parse_mode="HTML", reply_markup=dept_kb(fac)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("td:"))
async def dept_chosen(cb: CallbackQuery):
    _, fac, di_s = cb.data.split(":", 2)
    di       = int(di_s)
    depts    = depts_of_fac(fac)
    dept     = depts[di] if di < len(depts) else "?"
    teachers = teachers_of_dept(fac, di)
    if not teachers:
        await cb.answer("Викладачів не знайдено"); return
    total = len(teachers)
    await cb.message.edit_text(
        f"🏛 <b>{dept}</b>\n"
        f"<b>{fac}</b>  |  Викладачів: <b>{total}</b>\n\n"
        f"<i>Оберіть викладача:</i>",
        parse_mode="HTML",
        reply_markup=list_kb(fac, di, teachers, page=0)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tl:"))
async def turn_page(cb: CallbackQuery):
    _, fac, di_s, pg_s = cb.data.split(":", 3)
    di, pg   = int(di_s), int(pg_s)
    depts    = depts_of_fac(fac)
    dept     = depts[di] if di < len(depts) else "?"
    teachers = teachers_of_dept(fac, di)
    await cb.message.edit_text(
        f"🏛 <b>{dept}</b>\n"
        f"<b>{fac}</b>  |  Викладачів: <b>{len(teachers)}</b>\n\n"
        f"<i>Сторінка {pg+1}</i>",
        parse_mode="HTML",
        reply_markup=list_kb(fac, di, teachers, page=pg)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tc:"))
async def teacher_card_cb(cb: CallbackQuery):
    _, fac, di_s, ti_s = cb.data.split(":", 3)
    di, ti   = int(di_s), int(ti_s)
    teachers = teachers_of_dept(fac, di)
    if ti >= len(teachers):
        await cb.answer("❌ Не знайдено"); return
    t = teachers[ti]
    await cb.message.edit_text(
        teacher_card(t), parse_mode="HTML",
        reply_markup=teacher_action_kb(t, fac, di, ti),
        disable_web_page_preview=True
    )
    await cb.answer()


@router.callback_query(F.data.startswith("t_s:"))
async def search_start(cb: CallbackQuery, state: FSMContext):
    fac = cb.data.split(":",1)[1]
    await state.update_data(fac="" if fac=="all" else fac)
    await state.set_state(TS.search)
    scope = f"факультету <b>{fac}</b>" if fac != "all" else "університету"
    await cb.message.edit_text(
        f"🔍 Пошук по {scope}\n\nВведи прізвище або дисципліну:",
        parse_mode="HTML"
    )
    await cb.answer()


@router.message(TS.search)
async def do_search(message: Message, state: FSMContext):
    d   = await state.get_data()
    fac = d.get("fac","")
    await state.clear()
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("❌ Запит занадто короткий."); return
    results = find_teachers(q, fac)
    if not results:
        scope = f" на факультеті <b>{fac}</b>" if fac else ""
        await message.answer(
            f"🔍 За запитом <b>{q}</b>{scope} нічого не знайдено.\n\n"
            f"Спробуй інше прізвище або назву дисципліни.",
            parse_mode="HTML", reply_markup=fac_kb()
        ); return

    total = len(results)
    scope = f" · {fac}" if fac else ""
    await message.answer(
        f"🔍 <b>Результати пошуку «{q}»{scope}</b>\n"
        f"Знайдено: <b>{total}</b> викладач(ів)",
        parse_mode="HTML"
    )

    for t in results[:8]:
        enc  = urllib.parse.quote(f"{t.get('name','')} ТНТУ")
        btns = []
        if t.get("schedule_url"):
            btns.append([InlineKeyboardButton(
                text="📅 Розклад на сайті ТНТУ",
                url=t["schedule_url"]
            )])
        btns.append([InlineKeyboardButton(
            text="🔍 Знайти у Google",
            url=f"https://www.google.com/search?q={enc}"
        )])
        kb = InlineKeyboardMarkup(inline_keyboard=btns)
        await message.answer(
            teacher_card(t), parse_mode="HTML",
            reply_markup=kb, disable_web_page_preview=True
        )

    if total > 8:
        await message.answer(
            f"<i>...і ще {total-8}. Уточни запит для кращого результату.</i>",
            parse_mode="HTML", reply_markup=fac_kb()
        )