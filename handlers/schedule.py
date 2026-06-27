import json, os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import FACULTIES, TNTU_BASE_URL
from scrapers.schedule_scraper import get_faculty_data, get_exam_schedule, get_schedule_pdfs

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

def fac_kb(mode):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=n, callback_data=f"sc_f:{mode}:{c}")]
        for n,c in FACULTIES.items()
    ])

def course_kb(mode, fac, courses):
    btns = [[InlineKeyboardButton(text=c, callback_data=f"sc_c:{mode}:{fac}:{c}")] for c in courses]
    btns.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"sc_bk:f:{mode}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def group_kb(mode, fac, course, groups):
    btns, row = [], []
    for n,c in groups:
        row.append(InlineKeyboardButton(text=n, callback_data=f"sc_g:{mode}:{fac}:{course}:{c}:{n}"))
        if len(row) == 3: btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"sc_c:{mode}:{fac}:{course}")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def saved_kb(mode, g):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📌 {g['group_name']}",
         callback_data=f"sc_s:{mode}:{g['faculty']}:{g['group_code']}:{g['group_name']}")],
        [InlineKeyboardButton(text="🔍 Інша група", callback_data=f"sc_bk:f:{mode}")],
    ])

async def show(msg, mode, fac, code, name):
    if mode == "exam":
        text = get_exam_schedule(code, name)
    else:
        text = get_schedule_pdfs(fac, name)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    await msg.edit_text(chunks[0], parse_mode="HTML", disable_web_page_preview=True)
    for ch in chunks[1:]:
        await msg.answer(ch, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "📅 Розклад занять")
async def sched_menu(message: Message):
    s = get_u(message.from_user.id)
    title = "📅 <b>Розклад занять</b>"
    if s:
        await message.answer(f"{title}\n\nОберіть групу:", parse_mode="HTML",
                             reply_markup=saved_kb("pdf", s))
    else:
        await message.answer(f"{title}\n\nОберіть факультет:", parse_mode="HTML",
                             reply_markup=fac_kb("pdf"))

@router.message(F.text == "📝 Розклад екзаменів")
async def exam_menu(message: Message):
    s = get_u(message.from_user.id)
    title = "📝 <b>Розклад екзаменів</b>"
    if s:
        await message.answer(f"{title}\n\nОберіть групу:", parse_mode="HTML",
                             reply_markup=saved_kb("exam", s))
    else:
        await message.answer(f"{title}\n\nОберіть факультет:", parse_mode="HTML",
                             reply_markup=fac_kb("exam"))

@router.callback_query(F.data.startswith("sc_bk:f:"))
async def bk_fac(cb: CallbackQuery):
    mode = cb.data.split(":")[-1]
    title = "📅 <b>Розклад занять</b>" if mode == "pdf" else "📝 <b>Розклад екзаменів</b>"
    await cb.message.edit_text(f"{title}\n\nОберіть факультет:",
                               parse_mode="HTML", reply_markup=fac_kb(mode))
    await cb.answer()

@router.callback_query(F.data.startswith("sc_f:"))
async def fac(cb: CallbackQuery):
    _, mode, fac_code = cb.data.split(":",2)
    fac_name = next((k for k,v in FACULTIES.items() if v==fac_code), fac_code)
    await cb.message.edit_text(f"⏳ Завантажую {fac_name}...", parse_mode="HTML")
    await cb.answer()
    data = get_faculty_data(fac_code)
    gbс = data.get("groups_by_course", {})
    if not gbс:
        await cb.message.edit_text(
            f"❌ Не вдалося завантажити групи {fac_name}.\n\n"
            f"🔗 <a href=\"{TNTU_BASE_URL}/?p=uk/schedule&s={fac_code}\">Сайт ТНТУ</a>",
            parse_mode="HTML"); return
    await cb.message.edit_text(
        f"📚 <b>{fac_name}</b>\n\nОберіть курс:", parse_mode="HTML",
        reply_markup=course_kb(mode, fac_code, list(gbс.keys())))

@router.callback_query(F.data.startswith("sc_c:"))
async def course(cb: CallbackQuery):
    parts = cb.data.split(":",3)
    _, mode, fac_code, crs = parts
    fac_name = next((k for k,v in FACULTIES.items() if v==fac_code), fac_code)
    data = get_faculty_data(fac_code)
    groups = data.get("groups_by_course",{}).get(crs,[])
    if not groups:
        await cb.message.edit_text(f"❌ Груп для {crs} не знайдено.")
        await cb.answer(); return
    await cb.message.edit_text(
        f"📚 <b>{fac_name} — {crs}</b>\n\nОберіть групу:", parse_mode="HTML",
        reply_markup=group_kb(mode, fac_code, crs, groups))
    await cb.answer()

@router.callback_query(F.data.startswith("sc_g:"))
async def grp(cb: CallbackQuery):
    parts = cb.data.split(":")
    mode,fac,crs,code,name = parts[1],parts[2],parts[3],parts[4],parts[5]
    save_u(cb.from_user.id, fac, name, code)
    await cb.message.edit_text(f"⏳ Завантажую для групи <b>{name}</b>...", parse_mode="HTML")
    await cb.answer()
    await show(cb.message, mode, fac, code, name)

@router.callback_query(F.data.startswith("sc_s:"))
async def saved(cb: CallbackQuery):
    parts = cb.data.split(":",4)
    mode,fac,code,name = parts[1],parts[2],parts[3],parts[4]
    await cb.message.edit_text(f"⏳ Завантажую для групи <b>{name}</b>...", parse_mode="HTML")
    await cb.answer()
    await show(cb.message, mode, fac, code, name)