import json, os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/notes.json"

class NS(StatesGroup):
    text = State()

def load() -> dict:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {}

def save(d: dict):
    os.makedirs("data", exist_ok=True)
    json.dump(d, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def get_notes(uid: int) -> list:
    return load().get(str(uid), [])

def add_note(uid: int, text: str):
    d = load()
    k = str(uid)
    d.setdefault(k, [])
    d[k].append({"id": len(d[k])+1, "text": text,
                 "created": datetime.now().strftime("%d.%m.%Y %H:%M")})
    for i, n in enumerate(d[k], 1): n["id"] = i
    save(d)

def del_note(uid: int, nid: int) -> bool:
    d = load(); k = str(uid)
    before = len(d.get(k, []))
    d[k] = [n for n in d.get(k, []) if n["id"] != nid]
    for i, n in enumerate(d[k], 1): n["id"] = i
    save(d)
    return len(d[k]) < before

def notes_kb(notes: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"🗑 #{n['id']}", callback_data=f"del_note:{n['id']}")]
               for n in notes]
    buttons.append([InlineKeyboardButton(text="✏️ Додати нотатку", callback_data="add_note")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def render(notes: list) -> str:
    if not notes:
        return "📝 <b>Нотатки</b>\n\nПоки порожньо."
    lines = [f"📝 <b>Мої нотатки</b> ({len(notes)})\n{'─'*22}"]
    for n in notes:
        lines.append(f"<b>#{n['id']}</b> {n['text']}\n<i>📅 {n['created']}</i>")
    return "\n\n".join(lines)

@router.message(F.text == "📝 Нотатки")
async def notes_menu(message: Message, state: FSMContext):
    await state.clear()
    notes = get_notes(message.from_user.id)
    await message.answer(render(notes), reply_markup=notes_kb(notes), parse_mode="HTML")

@router.callback_query(F.data == "add_note")
async def add_prompt(cb: CallbackQuery, state: FSMContext):
    await state.set_state(NS.text)
    await cb.message.answer("✏️ Напиши текст нотатки:")
    await cb.answer()

@router.message(NS.text)
async def save_note(message: Message, state: FSMContext):
    await state.clear()
    t = message.text.strip()
    if len(t) < 2: await message.answer("❌ Занадто коротко."); return
    add_note(message.from_user.id, t)
    await message.answer("✅ <b>Нотатку збережено!</b>", parse_mode="HTML")

@router.callback_query(F.data.startswith("del_note:"))
async def del_note_cb(cb: CallbackQuery):
    nid = int(cb.data.split(":")[1])
    del_note(cb.from_user.id, nid)
    notes = get_notes(cb.from_user.id)
    await cb.message.edit_text(render(notes), reply_markup=notes_kb(notes), parse_mode="HTML")
    await cb.answer(f"🗑 Нотатку #{nid} видалено")