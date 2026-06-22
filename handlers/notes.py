import json
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
NOTES_FILE = "data/notes.json"


class NoteStates(StatesGroup):
    waiting_for_text = State()


# ─── JSON утиліти ────────────────────────────────────────────────────────────

def load_notes() -> dict:
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_notes(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_notes(user_id: int) -> list[dict]:
    return load_notes().get(str(user_id), [])


def add_note(user_id: int, text: str):
    data = load_notes()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append({
        "id": len(data[uid]) + 1,
        "text": text,
        "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })
    # Перенумеровуємо id
    for i, note in enumerate(data[uid], 1):
        note["id"] = i
    save_notes(data)


def delete_note(user_id: int, note_id: int) -> bool:
    data = load_notes()
    uid = str(user_id)
    notes = data.get(uid, [])
    new_notes = [n for n in notes if n["id"] != note_id]
    if len(new_notes) == len(notes):
        return False
    # Перенумеровуємо
    for i, note in enumerate(new_notes, 1):
        note["id"] = i
    data[uid] = new_notes
    save_notes(data)
    return True


# ─── Клавіатури ──────────────────────────────────────────────────────────────

def notes_keyboard(notes: list[dict]) -> InlineKeyboardMarkup:
    """Кнопки видалення для кожної нотатки."""
    buttons = [
        [InlineKeyboardButton(
            text=f"🗑 Видалити #{n['id']}",
            callback_data=f"del_note:{n['id']}"
        )]
        for n in notes
    ]
    buttons.append([InlineKeyboardButton(text="✏️ Додати нотатку", callback_data="add_note")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "📝 Нотатки")
async def notes_menu(message: Message, state: FSMContext):
    await state.clear()
    notes = get_user_notes(message.from_user.id)

    if not notes:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Додати першу нотатку", callback_data="add_note")]
        ])
        await message.answer(
            "📝 *Твої нотатки*\n\nПоки нотаток немає. Додай першу!",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    lines = ["📝 *Твої нотатки:*\n"]
    for n in notes:
        lines.append(f"*#{n['id']}* — {n['text']}\n_📅 {n['created']}_")

    await message.answer(
        "\n\n".join(lines),
        reply_markup=notes_keyboard(notes),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_note")
async def add_note_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NoteStates.waiting_for_text)
    await callback.message.answer(
        "✏️ Напиши текст нотатки:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(NoteStates.waiting_for_text)
async def save_note_handler(message: Message, state: FSMContext):
    await state.clear()
    text = message.text.strip()

    if len(text) < 2:
        await message.answer("❌ Нотатка занадто коротка.")
        return

    if len(text) > 500:
        await message.answer("❌ Нотатка занадто довга (макс. 500 символів).")
        return

    add_note(message.from_user.id, text)
    await message.answer(
        "✅ Нотатку збережено!\n\nНадішли *📝 Нотатки* щоб переглянути всі.",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("del_note:"))
async def delete_note_handler(callback: CallbackQuery):
    note_id = int(callback.data.split(":")[1])
    success = delete_note(callback.from_user.id, note_id)

    if success:
        await callback.answer(f"🗑 Нотатку #{note_id} видалено")
        # Оновлюємо список
        notes = get_user_notes(callback.from_user.id)
        if not notes:
            await callback.message.edit_text(
                "📝 *Твої нотатки*\n\nВсі нотатки видалено.",
                parse_mode="Markdown"
            )
        else:
            lines = ["📝 *Твої нотатки:*\n"]
            for n in notes:
                lines.append(f"*#{n['id']}* — {n['text']}\n_📅 {n['created']}_")
            await callback.message.edit_text(
                "\n\n".join(lines),
                reply_markup=notes_keyboard(notes),
                parse_mode="Markdown"
            )
    else:
        await callback.answer("❌ Нотатку не знайдено")
