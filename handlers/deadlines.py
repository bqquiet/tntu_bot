import json
import os
from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
DEADLINES_FILE = "data/deadlines.json"


class DeadlineStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_task    = State()
    waiting_for_date    = State()


# ─── JSON утиліти ────────────────────────────────────────────────────────────

def load_deadlines() -> dict:
    if os.path.exists(DEADLINES_FILE):
        with open(DEADLINES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_deadlines(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(DEADLINES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_deadlines(user_id: int) -> list[dict]:
    return load_deadlines().get(str(user_id), [])


def add_deadline(user_id: int, subject: str, task: str, due_date: str):
    data = load_deadlines()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append({
        "id": len(data[uid]) + 1,
        "subject": subject,
        "task": task,
        "due_date": due_date,  # формат: DD.MM.YYYY
        "done": False,
    })
    for i, d in enumerate(data[uid], 1):
        d["id"] = i
    save_deadlines(data)


def mark_done(user_id: int, deadline_id: int) -> bool:
    data = load_deadlines()
    uid = str(user_id)
    for d in data.get(uid, []):
        if d["id"] == deadline_id:
            d["done"] = True
            save_deadlines(data)
            return True
    return False


def delete_deadline(user_id: int, deadline_id: int):
    data = load_deadlines()
    uid = str(user_id)
    data[uid] = [d for d in data.get(uid, []) if d["id"] != deadline_id]
    for i, d in enumerate(data[uid], 1):
        d["id"] = i
    save_deadlines(data)


def days_until(due_date_str: str) -> int | None:
    try:
        due = datetime.strptime(due_date_str, "%d.%m.%Y").date()
        return (due - date.today()).days
    except ValueError:
        return None


def deadline_emoji(days: int | None) -> str:
    if days is None:
        return "📋"
    if days < 0:
        return "🔴"   # прострочено
    if days == 0:
        return "🚨"   # сьогодні
    if days == 1:
        return "⚠️"   # завтра
    if days <= 3:
        return "🟡"   # скоро
    return "🟢"       # є час


def format_deadlines(deadlines: list[dict], show_done: bool = False) -> str:
    active = [d for d in deadlines if not d["done"] or show_done]
    if not active:
        return "📋 *Дедлайни*\n\nНемає активних дедлайнів! 🎉"

    lines = ["📋 *Твої дедлайни:*\n"]
    for d in sorted(active, key=lambda x: datetime.strptime(x["due_date"], "%d.%m.%Y")):
        days = days_until(d["due_date"])
        emoji = deadline_emoji(days)
        done_mark = "~~" if d["done"] else ""

        if days is None:
            when = d["due_date"]
        elif days < 0:
            when = f"{d['due_date']} (прострочено на {abs(days)} дн.)"
        elif days == 0:
            when = f"{d['due_date']} (сьогодні!)"
        elif days == 1:
            when = f"{d['due_date']} (завтра!)"
        else:
            when = f"{d['due_date']} (через {days} дн.)"

        lines.append(
            f"{emoji} *#{d['id']}* {done_mark}{d['subject']}{done_mark}\n"
            f"   📌 {d['task']}\n"
            f"   📅 {when}"
        )
    return "\n\n".join(lines)


# ─── Клавіатури ──────────────────────────────────────────────────────────────

def deadlines_keyboard(deadlines: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    active = [d for d in deadlines if not d["done"]]
    for d in active[:8]:  # максимум 8 кнопок
        buttons.append([
            InlineKeyboardButton(text=f"✅ #{d['id']} виконано", callback_data=f"dl_done:{d['id']}"),
            InlineKeyboardButton(text=f"🗑 #{d['id']}", callback_data=f"dl_del:{d['id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="➕ Додати дедлайн", callback_data="dl_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Дедлайни")
async def deadlines_menu(message: Message, state: FSMContext):
    await state.clear()
    deadlines = get_user_deadlines(message.from_user.id)

    text = format_deadlines(deadlines)
    kb = deadlines_keyboard(deadlines)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "dl_add")
async def deadline_add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeadlineStates.waiting_for_subject)
    await callback.message.answer(
        "➕ *Новий дедлайн*\n\nКрок 1/3 — Введи назву предмету:\n_Наприклад: Програмування_",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(DeadlineStates.waiting_for_subject)
async def deadline_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text.strip())
    await state.set_state(DeadlineStates.waiting_for_task)
    await message.answer(
        "Крок 2/3 — Що потрібно здати?\n_Наприклад: Лабораторна робота №3_",
        parse_mode="Markdown"
    )


@router.message(DeadlineStates.waiting_for_task)
async def deadline_task(message: Message, state: FSMContext):
    await state.update_data(task=message.text.strip())
    await state.set_state(DeadlineStates.waiting_for_date)
    await message.answer(
        "Крок 3/3 — Введи дату здачі у форматі *ДД.ММ.РРРР*:\n_Наприклад: 25.06.2026_",
        parse_mode="Markdown"
    )


@router.message(DeadlineStates.waiting_for_date)
async def deadline_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await message.answer("❌ Невірний формат. Введи дату як *ДД.ММ.РРРР*", parse_mode="Markdown")
        return

    data = await state.get_data()
    await state.clear()

    add_deadline(message.from_user.id, data["subject"], data["task"], date_str)
    days = days_until(date_str)
    emoji = deadline_emoji(days)

    await message.answer(
        f"✅ Дедлайн додано!\n\n"
        f"{emoji} *{data['subject']}*\n"
        f"📌 {data['task']}\n"
        f"📅 {date_str}",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("dl_done:"))
async def deadline_done(callback: CallbackQuery):
    dl_id = int(callback.data.split(":")[1])
    success = mark_done(callback.from_user.id, dl_id)
    if success:
        await callback.answer(f"✅ Дедлайн #{dl_id} позначено як виконаний!")
        deadlines = get_user_deadlines(callback.from_user.id)
        await callback.message.edit_text(
            format_deadlines(deadlines),
            reply_markup=deadlines_keyboard(deadlines),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Не знайдено")


@router.callback_query(F.data.startswith("dl_del:"))
async def deadline_delete(callback: CallbackQuery):
    dl_id = int(callback.data.split(":")[1])
    delete_deadline(callback.from_user.id, dl_id)
    await callback.answer(f"🗑 Дедлайн #{dl_id} видалено")
    deadlines = get_user_deadlines(callback.from_user.id)
    await callback.message.edit_text(
        format_deadlines(deadlines),
        reply_markup=deadlines_keyboard(deadlines),
        parse_mode="Markdown"
    )


# ─── Функція для APScheduler (ранкові нагадування) ───────────────────────────

async def send_morning_deadlines(bot):
    """
    Надсилає всім користувачам їхні дедлайни на сьогодні і наступні 3 дні.
    Викликається APScheduler щодня о 08:00.
    """
    data = load_deadlines()
    for uid, deadlines in data.items():
        urgent = [
            d for d in deadlines
            if not d["done"] and days_until(d["due_date"]) is not None
            and 0 <= days_until(d["due_date"]) <= 3
        ]
        if not urgent:
            continue

        lines = ["⏰ *Нагадування про дедлайни*\n"]
        for d in urgent:
            days = days_until(d["due_date"])
            emoji = deadline_emoji(days)
            when = "сьогодні!" if days == 0 else ("завтра!" if days == 1 else f"через {days} дні")
            lines.append(f"{emoji} *{d['subject']}* — {d['task']}\n   📅 {d['due_date']} ({when})")

        try:
            await bot.send_message(int(uid), "\n\n".join(lines), parse_mode="Markdown")
        except Exception:
            pass  # користувач заблокував бота
