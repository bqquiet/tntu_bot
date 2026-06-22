import json
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
REMINDERS_FILE = "data/reminders.json"


class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_datetime = State()


# ─── JSON утиліти ────────────────────────────────────────────────────────────

def load_reminders() -> dict:
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_reminders(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_reminders(user_id: int) -> list[dict]:
    return load_reminders().get(str(user_id), [])


def add_reminder(user_id: int, text: str, remind_at: str) -> int:
    data = load_reminders()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    new_id = max((r["id"] for r in data[uid]), default=0) + 1
    data[uid].append({
        "id": new_id,
        "text": text,
        "remind_at": remind_at,  # формат: DD.MM.YYYY HH:MM
        "sent": False,
    })
    save_reminders(data)
    return new_id


def delete_reminder(user_id: int, reminder_id: int):
    data = load_reminders()
    uid = str(user_id)
    data[uid] = [r for r in data.get(uid, []) if r["id"] != reminder_id]
    save_reminders(data)


# ─── Клавіатура ──────────────────────────────────────────────────────────────

def reminders_keyboard(reminders: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for r in reminders[:8]:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 #{r['id']} — {r['text'][:20]}...",
                callback_data=f"rem_del:{r['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Додати нагадування", callback_data="rem_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "⏰ Нагадування")
async def reminders_menu(message: Message, state: FSMContext):
    await state.clear()
    reminders = [r for r in get_user_reminders(message.from_user.id) if not r["sent"]]

    if not reminders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати нагадування", callback_data="rem_add")]
        ])
        await message.answer(
            "⏰ *Нагадування*\n\nАктивних нагадувань немає.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return

    lines = ["⏰ *Твої нагадування:*\n"]
    for r in reminders:
        lines.append(f"🔔 *#{r['id']}* — {r['text']}\n   📅 {r['remind_at']}")

    await message.answer(
        "\n\n".join(lines),
        reply_markup=reminders_keyboard(reminders),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "rem_add")
async def reminder_add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ReminderStates.waiting_for_text)
    await callback.message.answer(
        "🔔 *Нове нагадування*\n\nКрок 1/2 — Про що нагадати?\n_Наприклад: Здати лабораторну №3_",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(ReminderStates.waiting_for_text)
async def reminder_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    await state.set_state(ReminderStates.waiting_for_datetime)
    await message.answer(
        "Крок 2/2 — Коли нагадати?\n\n"
        "Введи дату і час у форматі *ДД.ММ.РРРР ГГ:ХХ*\n"
        "_Наприклад: 25.06.2026 09:00_",
        parse_mode="Markdown"
    )


@router.message(ReminderStates.waiting_for_datetime)
async def reminder_datetime(message: Message, state: FSMContext):
    dt_str = message.text.strip()
    try:
        remind_dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Невірний формат. Введи як *ДД.ММ.РРРР ГГ:ХХ*\n_Наприклад: 25.06.2026 09:00_",
            parse_mode="Markdown"
        )
        return

    if remind_dt < datetime.now():
        await message.answer("❌ Ця дата вже в минулому. Введи майбутню дату.")
        return

    data = await state.get_data()
    await state.clear()

    add_reminder(message.from_user.id, data["text"], dt_str)
    await message.answer(
        f"✅ Нагадування встановлено!\n\n"
        f"🔔 *{data['text']}*\n"
        f"📅 {dt_str}",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("rem_del:"))
async def reminder_delete(callback: CallbackQuery):
    rem_id = int(callback.data.split(":")[1])
    delete_reminder(callback.from_user.id, rem_id)
    await callback.answer(f"🗑 Нагадування #{rem_id} видалено")

    reminders = [r for r in get_user_reminders(callback.from_user.id) if not r["sent"]]
    if not reminders:
        await callback.message.edit_text(
            "⏰ *Нагадування*\n\nАктивних нагадувань немає.",
            parse_mode="Markdown"
        )
    else:
        lines = ["⏰ *Твої нагадування:*\n"]
        for r in reminders:
            lines.append(f"🔔 *#{r['id']}* — {r['text']}\n   📅 {r['remind_at']}")
        await callback.message.edit_text(
            "\n\n".join(lines),
            reply_markup=reminders_keyboard(reminders),
            parse_mode="Markdown"
        )


# ─── Функція для APScheduler ─────────────────────────────────────────────────

async def check_and_send_reminders(bot):
    """
    Перевіряє всі нагадування і надсилає ті що настали.
    APScheduler викликає цю функцію щохвилини.
    """
    now = datetime.now()
    data = load_reminders()
    changed = False

    for uid, reminders in data.items():
        for r in reminders:
            if r["sent"]:
                continue
            try:
                remind_dt = datetime.strptime(r["remind_at"], "%d.%m.%Y %H:%M")
            except ValueError:
                continue

            if remind_dt <= now:
                try:
                    await bot.send_message(
                        int(uid),
                        f"🔔 *Нагадування!*\n\n{r['text']}",
                        parse_mode="Markdown"
                    )
                    r["sent"] = True
                    changed = True
                except Exception:
                    pass

    if changed:
        save_reminders(data)
