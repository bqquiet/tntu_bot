import json, os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/reminders.json"

class RS(StatesGroup):
    text = State()
    dt   = State()

def load() -> dict:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {}

def save(d: dict):
    os.makedirs("data", exist_ok=True)
    json.dump(d, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def get_active(uid: int) -> list:
    return [r for r in load().get(str(uid), []) if not r.get("sent")]

def rem_kb(rems: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"🗑 #{r['id']} {r['text'][:20]}",
                                     callback_data=f"rem_del:{r['id']}")]
               for r in rems[:8]]
    buttons.append([InlineKeyboardButton(text="➕ Додати нагадування", callback_data="rem_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def render(rems: list) -> str:
    if not rems:
        return "⏰ <b>Нагадування</b>\n\nАктивних нагадувань немає."
    lines = [f"⏰ <b>Мої нагадування</b> ({len(rems)})\n{'─'*22}"]
    for r in rems:
        lines.append(f"🔔 <b>#{r['id']}</b> {r['text']}\n<i>📅 {r['remind_at']}</i>")
    return "\n\n".join(lines)

@router.message(F.text == "⏰ Нагадування")
async def rem_menu(message: Message, state: FSMContext):
    await state.clear()
    rems = get_active(message.from_user.id)
    await message.answer(render(rems), reply_markup=rem_kb(rems), parse_mode="HTML")

@router.callback_query(F.data == "rem_add")
async def rem_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(RS.text)
    await cb.message.answer(
        "🔔 <b>Нове нагадування</b>\n\nКрок 1/2 — Про що нагадати?",
        parse_mode="HTML")
    await cb.answer()

@router.message(RS.text)
async def rem_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    await state.set_state(RS.dt)
    await message.answer(
        "Крок 2/2 — Коли? (<code>ДД.ММ.РРРР ГГ:ХХ</code>)\n"
        "<i>Приклад: 25.06.2026 09:00</i>", parse_mode="HTML")

@router.message(RS.dt)
async def rem_dt(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Формат: <code>ДД.ММ.РРРР ГГ:ХХ</code>", parse_mode="HTML")
        return
    if dt < datetime.now():
        await message.answer("❌ Дата в минулому. Введи майбутню.")
        return
    d = await state.get_data()
    await state.clear()
    data = load(); k = str(message.from_user.id)
    data.setdefault(k, [])
    nid = max((r["id"] for r in data[k]), default=0) + 1
    data[k].append({"id":nid,"text":d["text"],"remind_at":message.text.strip(),"sent":False})
    save(data)
    await message.answer(
        f"✅ <b>Нагадування встановлено!</b>\n\n🔔 {d['text']}\n📅 {message.text.strip()}",
        parse_mode="HTML")

@router.callback_query(F.data.startswith("rem_del:"))
async def rem_del(cb: CallbackQuery):
    nid = int(cb.data.split(":")[1])
    d = load(); k = str(cb.from_user.id)
    d[k] = [r for r in d.get(k,[]) if r["id"] != nid]
    save(d)
    rems = get_active(cb.from_user.id)
    await cb.message.edit_text(render(rems), reply_markup=rem_kb(rems), parse_mode="HTML")
    await cb.answer(f"🗑 #{nid} видалено")

async def check_and_send_reminders(bot):
    now = datetime.now()
    d = load(); changed = False
    for uid, rems in d.items():
        for r in rems:
            if r.get("sent"): continue
            try:
                if datetime.strptime(r["remind_at"], "%d.%m.%Y %H:%M") <= now:
                    await bot.send_message(int(uid),
                        f"🔔 <b>Нагадування!</b>\n\n{r['text']}", parse_mode="HTML")
                    r["sent"] = True; changed = True
            except Exception:
                pass
    if changed: save(d)