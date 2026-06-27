import json, os
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/deadlines.json"

class DS(StatesGroup):
    subj = State()
    task = State()
    dt   = State()

def load() -> dict:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {}

def save(d: dict):
    os.makedirs("data", exist_ok=True)
    json.dump(d, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def days_left(s: str) -> int | None:
    try:
        return (datetime.strptime(s, "%d.%m.%Y").date() - date.today()).days
    except: return None

def status(days):
    if days is None: return "📋","?"
    if days < 0:  return "🔴", f"прострочено на {abs(days)} дн."
    if days == 0: return "🚨", "сьогодні!"
    if days == 1: return "⚠️", "завтра!"
    if days <= 3: return "🟡", f"через {days} дні"
    return "🟢", f"через {days} дн."

def get_dl(uid: int) -> list:
    return load().get(str(uid), [])

def render(dls: list) -> str:
    active = [d for d in dls if not d.get("done")]
    if not active:
        return "📋 <b>Дедлайни</b>\n\nАктивних дедлайнів немає 🎉"
    lines = [f"📋 <b>Мої дедлайни</b> ({len(active)})\n{'─'*22}"]
    for d in sorted(active, key=lambda x: datetime.strptime(x["due_date"],"%d.%m.%Y")):
        em, when = status(days_left(d["due_date"]))
        lines.append(
            f"{em} <b>#{d['id']}</b> {d['subject']}\n"
            f"   📌 {d['task']}\n"
            f"   📅 {d['due_date']} — <i>{when}</i>"
        )
    return "\n\n".join(lines)

def dl_kb(dls: list) -> InlineKeyboardMarkup:
    active = [d for d in dls if not d.get("done")]
    buttons = []
    for d in active[:6]:
        buttons.append([
            InlineKeyboardButton(text=f"✅ #{d['id']}", callback_data=f"dl_done:{d['id']}"),
            InlineKeyboardButton(text=f"🗑 #{d['id']}", callback_data=f"dl_del:{d['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Додати дедлайн", callback_data="dl_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "📋 Дедлайни")
async def dl_menu(message: Message, state: FSMContext):
    await state.clear()
    dls = get_dl(message.from_user.id)
    await message.answer(render(dls), reply_markup=dl_kb(dls), parse_mode="HTML")

@router.callback_query(F.data == "dl_add")
async def dl_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(DS.subj)
    await cb.message.answer(
        "➕ <b>Новий дедлайн</b>\n\n1/3 — Назва предмету:", parse_mode="HTML")
    await cb.answer()

@router.message(DS.subj)
async def dl_subj(message: Message, state: FSMContext):
    await state.update_data(subj=message.text.strip())
    await state.set_state(DS.task)
    await message.answer("2/3 — Що здати?")

@router.message(DS.task)
async def dl_task(message: Message, state: FSMContext):
    await state.update_data(task=message.text.strip())
    await state.set_state(DS.dt)
    await message.answer("3/3 — Дата здачі (<code>ДД.ММ.РРРР</code>):", parse_mode="HTML")

@router.message(DS.dt)
async def dl_date(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Формат: <code>ДД.ММ.РРРР</code>", parse_mode="HTML")
        return
    d = await state.get_data()
    await state.clear()
    data = load(); k = str(message.from_user.id)
    data.setdefault(k, [])
    nid = len(data[k]) + 1
    data[k].append({"id":nid,"subject":d["subj"],"task":d["task"],
                    "due_date":message.text.strip(),"done":False})
    for i,x in enumerate(data[k],1): x["id"] = i
    save(data)
    em, when = status(days_left(message.text.strip()))
    await message.answer(
        f"✅ <b>Дедлайн додано!</b>\n\n"
        f"{em} <b>{d['subj']}</b>\n📌 {d['task']}\n📅 {message.text.strip()} — <i>{when}</i>",
        parse_mode="HTML")

@router.callback_query(F.data.startswith("dl_done:"))
async def dl_done(cb: CallbackQuery):
    nid = int(cb.data.split(":")[1])
    d = load(); k = str(cb.from_user.id)
    for x in d.get(k,[]): 
        if x["id"] == nid: x["done"] = True
    save(d)
    await cb.answer(f"✅ #{nid} виконано!")
    dls = get_dl(cb.from_user.id)
    await cb.message.edit_text(render(dls), reply_markup=dl_kb(dls), parse_mode="HTML")

@router.callback_query(F.data.startswith("dl_del:"))
async def dl_del(cb: CallbackQuery):
    nid = int(cb.data.split(":")[1])
    d = load(); k = str(cb.from_user.id)
    d[k] = [x for x in d.get(k,[]) if x["id"] != nid]
    for i,x in enumerate(d[k],1): x["id"] = i
    save(d)
    await cb.answer(f"🗑 #{nid} видалено")
    dls = get_dl(cb.from_user.id)
    await cb.message.edit_text(render(dls), reply_markup=dl_kb(dls), parse_mode="HTML")

async def send_morning_deadlines(bot):
    d = load()
    for uid, dls in d.items():
        urgent = [x for x in dls if not x.get("done")
                  and days_left(x["due_date"]) is not None
                  and 0 <= days_left(x["due_date"]) <= 3]
        if not urgent: continue
        lines = ["⏰ <b>Нагадування про дедлайни</b>\n"]
        for x in urgent:
            em, when = status(days_left(x["due_date"]))
            lines.append(f"{em} <b>{x['subject']}</b> — {x['task']}\n📅 {x['due_date']} ({when})")
        try:
            await bot.send_message(int(uid), "\n\n".join(lines), parse_mode="HTML")
        except: pass