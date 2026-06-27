import json, os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/teachers.json"
FACULTIES = ["ФІС","ФПТ","ФМТ","ФЕМ"]


class TS(StatesGroup):
    query = State()


def load() -> list[dict]:
    if not os.path.exists(FILE):
        return []
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)


def search(q: str, fac: str = "") -> list[dict]:
    q = q.lower()
    return [
        t for t in load()
        if (not fac or t.get("faculty") == fac)
        and q in " ".join([t.get("name",""), t.get("position",""),
                           t.get("department",""), *t.get("courses",[])]).lower()
    ]


def card(t: dict) -> str:
    lines = [f"👨‍🏫 <b>{t['name']}</b>"]
    if t.get("position"):
        lines.append(f"📌 <i>{t['position']}</i>")
    lines.append(f"🏛 {t['department']} · <b>{t.get('faculty','')}</b>")
    if t.get("email"):
        lines.append(f"📧 {t['email']}")
    if t.get("courses"):
        lines.append(f"📚 {', '.join(t['courses'])}")
    if t.get("consultation"):
        lines.append(f"🕐 {t['consultation']}")
    return "\n".join(lines)


def schedule_kb(t: dict) -> InlineKeyboardMarkup | None:
    if t.get("schedule_url"):
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📅 Розклад викладача", url=t["schedule_url"])
        ]])
    return None


def fac_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f, callback_data=f"tf:{f}") for f in FACULTIES[:2]],
        [InlineKeyboardButton(text=f, callback_data=f"tf:{f}") for f in FACULTIES[2:]],
        [InlineKeyboardButton(text="🔍 Пошук по всьому університету", callback_data="tf:all")],
    ])


def dept_kb(fac: str):
    all_t = load()
    depts = sorted(set(t["department"] for t in all_t if t.get("faculty") == fac))
    buttons = [
        [InlineKeyboardButton(text=d[:40], callback_data=f"td:{fac}:{i}")]
        for i, d in enumerate(depts)
    ]
    buttons.append([InlineKeyboardButton(text="🔍 Пошук по імені", callback_data=f"tf:{fac}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="tf:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons), depts


@router.message(F.text == "👨‍🏫 Викладачі")
async def menu(message: Message, state: FSMContext):
    await state.clear()
    n = len(load())
    await message.answer(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\nВ базі: <b>{n}</b> викладачів\n\nОберіть факультет:",
        reply_markup=fac_kb(), parse_mode="HTML"
    )


@router.callback_query(F.data == "tf:back")
async def back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    n = len(load())
    await cb.message.edit_text(
        f"👨‍🏫 <b>Викладачі ТНТУ</b>\n\nВ базі: <b>{n}</b> викладачів\n\nОберіть факультет:",
        reply_markup=fac_kb(), parse_mode="HTML"
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tf:"))
async def fac_chosen(cb: CallbackQuery, state: FSMContext):
    fac = cb.data.split(":",1)[1]
    if fac == "all":
        await state.update_data(fac="")
        await state.set_state(TS.query)
        await cb.message.edit_text(
            "🔍 <b>Пошук по всьому університету</b>\n\nВведи прізвище, ім'я або дисципліну:",
            parse_mode="HTML"
        )
        await cb.answer()
        return
    if fac == "back":
        return
    kb, depts = dept_kb(fac)
    n = sum(1 for t in load() if t.get("faculty") == fac)
    await cb.message.edit_text(
        f"👨‍🏫 <b>{fac}</b> — {n} викладачів\n\nОберіть кафедру:",
        reply_markup=kb, parse_mode="HTML"
    )
    await state.update_data(fac=fac, depts=depts)
    await cb.answer()


@router.callback_query(F.data.startswith("td:"))
async def dept_chosen(cb: CallbackQuery, state: FSMContext):
    _, fac, idx = cb.data.split(":", 2)
    data = await state.get_data()
    depts = data.get("depts", [])
    idx = int(idx)
    if idx >= len(depts):
        await cb.answer("❌")
        return
    dept = depts[idx]
    teachers = [t for t in load() if t.get("department") == dept]
    await cb.answer()
    await cb.message.edit_text(
        f"🏛 <b>{dept}</b>\nВикладачів: {len(teachers)}",
        parse_mode="HTML"
    )
    for t in teachers:
        kb = schedule_kb(t)
        await cb.message.answer(card(t), parse_mode="HTML",
                                reply_markup=kb if kb else None)


@router.message(TS.query)
async def do_search(message: Message, state: FSMContext):
    data = await state.get_data()
    fac = data.get("fac", "")
    await state.clear()
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("❌ Запит занадто короткий.")
        return
    results = search(q, fac)
    if not results:
        await message.answer(f"🔍 За запитом <b>{q}</b> нічого не знайдено.", parse_mode="HTML")
        return
    await message.answer(f"🔍 Знайдено: <b>{len(results)}</b>", parse_mode="HTML")
    for t in results[:5]:
        kb = schedule_kb(t)
        await message.answer(card(t), parse_mode="HTML", reply_markup=kb)
    if len(results) > 5:
        await message.answer(f"<i>...і ще {len(results)-5}. Уточни запит.</i>", parse_mode="HTML")