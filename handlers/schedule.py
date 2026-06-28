import json, os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import FACULTIES, TNTU_BASE_URL
from scrapers.schedule_scraper import get_faculty_data, get_full_schedule

router = Router()
FILE = "data/users.json"


def load_u() -> dict:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {}

def save_u(uid, fac, name, code):
    d = load_u(); d[str(uid)] = {"faculty":fac,"group_name":name,"group_code":code}
    os.makedirs("data", exist_ok=True)
    json.dump(d, open(FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def get_u(uid) -> dict | None:
    return load_u().get(str(uid))


def fac_kb(mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n, callback_data=f"sc_f:{mode}:{c}")]
        for n, c in FACULTIES.items()
    ])

def course_kb(mode: str, fac: str, courses: list) -> InlineKeyboardMarkup:
    btns = [[InlineKeyboardButton(text=c, callback_data=f"sc_c:{mode}:{fac}:{c}")] for c in courses]
    btns.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"sc_bk:{mode}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def group_kb(mode: str, fac: str, course: str, groups: list) -> InlineKeyboardMarkup:
    btns, row = [], []
    for n, c in groups:
        row.append(InlineKeyboardButton(text=n, callback_data=f"sc_g:{mode}:{fac}:{c}:{n}"))
        if len(row) == 3: btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"sc_c:{mode}:{fac}:{course}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def saved_kb(saved: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📌 {saved['group_name']} — показати розклад",
            callback_data=f"sc_show:{saved['faculty']}:{saved['group_code']}:{saved['group_name']}"
        )],
        [InlineKeyboardButton(text="🔍 Інша група", callback_data="sc_bk:full")],
    ])


async def show_schedule(msg, fac: str, code: str, name: str):
    """Завантажує і відправляє об'єднаний розклад."""
    text = get_full_schedule(code, name, fac)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    await msg.edit_text(chunks[0], parse_mode="HTML", disable_web_page_preview=True)
    for ch in chunks[1:]:
        await msg.answer(ch, parse_mode="HTML", disable_web_page_preview=True)


# ── Обидва входи ведуть до одного розкладу ───────────────────────────────────

@router.message(F.text == "📅 Розклад занять")
@router.message(F.text == "📝 Розклад екзаменів")
async def schedule_menu(message: Message):
    s = get_u(message.from_user.id)
    if s:
        await message.answer(
            "📋 <b>Розклад групи</b>\n\nОберіть дію:",
            parse_mode="HTML", reply_markup=saved_kb(s)
        )
    else:
        await message.answer(
            "📋 <b>Розклад</b>\n\nОберіть факультет:",
            parse_mode="HTML", reply_markup=fac_kb("full")
        )


@router.callback_query(F.data.startswith("sc_bk:"))
async def back_to_fac(cb: CallbackQuery):
    mode = cb.data.split(":", 1)[1]
    await cb.message.edit_text(
        "📋 <b>Розклад</b>\n\nОберіть факультет:",
        parse_mode="HTML", reply_markup=fac_kb(mode)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("sc_f:"))
async def fac_chosen(cb: CallbackQuery):
    _, mode, fac_code = cb.data.split(":", 2)
    fac_name = next((k for k,v in FACULTIES.items() if v == fac_code), fac_code)
    await cb.message.edit_text(f"⏳ Завантажую {fac_name}...", parse_mode="HTML")
    await cb.answer()
    data = get_faculty_data(fac_code)
    gbc  = data.get("groups_by_course", {})
    if not gbc:
        await cb.message.edit_text(
            f"❌ Не вдалося завантажити групи {fac_name}.\n\n"
            f"🔗 <a href=\"{TNTU_BASE_URL}/?p=uk/schedule&s={fac_code}\">Сайт ТНТУ</a>",
            parse_mode="HTML"
        ); return
    await cb.message.edit_text(
        f"📚 <b>{fac_name}</b>\n\nОберіть курс:",
        parse_mode="HTML",
        reply_markup=course_kb(mode, fac_code, list(gbc.keys()))
    )


@router.callback_query(F.data.startswith("sc_c:"))
async def course_chosen(cb: CallbackQuery):
    parts = cb.data.split(":", 3)
    _, mode, fac_code, crs = parts
    fac_name = next((k for k,v in FACULTIES.items() if v == fac_code), fac_code)
    data   = get_faculty_data(fac_code)
    groups = data.get("groups_by_course", {}).get(crs, [])
    if not groups:
        await cb.answer("❌ Груп не знайдено"); return
    await cb.message.edit_text(
        f"📚 <b>{fac_name} — {crs}</b>\n\nОберіть групу:",
        parse_mode="HTML",
        reply_markup=group_kb(mode, fac_code, crs, groups)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("sc_g:"))
async def group_chosen(cb: CallbackQuery):
    # sc_g:mode:fac:code:name
    parts      = cb.data.split(":", 4)
    mode, fac, code, name = parts[1], parts[2], parts[3], parts[4]
    save_u(cb.from_user.id, fac, name, code)
    await cb.message.edit_text(
        f"⏳ Завантажую розклад групи <b>{name}</b>...", parse_mode="HTML"
    )
    await cb.answer()
    await show_schedule(cb.message, fac, code, name)


@router.callback_query(F.data.startswith("sc_show:"))
async def show_saved(cb: CallbackQuery):
    # sc_show:fac:code:name
    parts      = cb.data.split(":", 3)
    fac, code, name = parts[1], parts[2], parts[3]
    await cb.message.edit_text(
        f"⏳ Завантажую розклад групи <b>{name}</b>...", parse_mode="HTML"
    )
    await cb.answer()
    await show_schedule(cb.message, fac, code, name)