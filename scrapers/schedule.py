import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import FACULTIES, TNTU_BASE_URL
from scrapers.schedule_scraper import get_faculty_groups, get_exam_schedule

router = Router()

USERS_FILE = "data/users.json"


# ─── Утиліти для збереження групи користувача ───────────────────────────────

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_user_group(user_id: int, faculty: str, group_name: str, group_code: str):
    users = load_users()
    users[str(user_id)] = {
        "faculty": faculty,
        "group_name": group_name,
        "group_code": group_code,
    }
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user_group(user_id: int) -> dict | None:
    users = load_users()
    return users.get(str(user_id))


# ─── Клавіатури ──────────────────────────────────────────────────────────────

def faculty_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"fac:{code}")]
        for name, code in FACULTIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_keyboard(faculty_code: str) -> InlineKeyboardMarkup:
    groups = get_faculty_groups(faculty_code)
    buttons = [
        [InlineKeyboardButton(text=course, callback_data=f"course:{faculty_code}:{course}")]
        for course in groups
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back:faculties")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def group_keyboard(faculty_code: str, course: str) -> InlineKeyboardMarkup:
    groups = get_faculty_groups(faculty_code)
    group_list = groups.get(course, [])
    # По 3 кнопки в рядку
    buttons = []
    row = []
    for name, code in group_list:
        row.append(InlineKeyboardButton(text=name, callback_data=f"group:{faculty_code}:{course}:{code}:{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"back:courses:{faculty_code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "📅 Розклад")
async def schedule_menu(message: Message):
    user_group = get_user_group(message.from_user.id)

    if user_group:
        # Якщо група збережена — пропонуємо швидкий вибір
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"📌 Моя група: {user_group['group_name']}",
                callback_data=f"exam_show:{user_group['group_code']}:{user_group['group_name']}"
            )],
            [InlineKeyboardButton(text="🔍 Інша група", callback_data="back:faculties")]
        ])
        await message.answer(
            "📅 *Розклад екзаменів*\n\nОберіть групу:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "📅 *Розклад екзаменів*\n\nОберіть факультет:",
            reply_markup=faculty_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "back:faculties")
async def back_to_faculties(callback: CallbackQuery):
    await callback.message.edit_text(
        "📅 *Розклад екзаменів*\n\nОберіть факультет:",
        reply_markup=faculty_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fac:"))
async def faculty_chosen(callback: CallbackQuery):
    faculty_code = callback.data.split(":")[1]
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code)

    await callback.message.edit_text(
        f"📅 *{faculty_name}*\n\nОберіть курс:",
        reply_markup=course_keyboard(faculty_code),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back:courses:"))
async def back_to_courses(callback: CallbackQuery):
    faculty_code = callback.data.split(":")[2]
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code)

    await callback.message.edit_text(
        f"📅 *{faculty_name}*\n\nОберіть курс:",
        reply_markup=course_keyboard(faculty_code),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("course:"))
async def course_chosen(callback: CallbackQuery):
    _, faculty_code, course = callback.data.split(":", 2)
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code)

    await callback.message.edit_text(
        f"📅 *{faculty_name} · {course}*\n\nОберіть групу:",
        reply_markup=group_keyboard(faculty_code, course),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("group:"))
async def group_chosen(callback: CallbackQuery):
    parts = callback.data.split(":")
    faculty_code = parts[1]
    course = parts[2]
    group_code = parts[3]
    group_name = parts[4]

    # Зберігаємо групу користувача
    save_user_group(callback.from_user.id, faculty_code, group_name, group_code)

    await callback.message.edit_text(
        f"⏳ Завантажую розклад для *{group_name}*...",
        parse_mode="Markdown"
    )
    await callback.answer()

    schedule_text = get_exam_schedule(group_code)
    await callback.message.edit_text(schedule_text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("exam_show:"))
async def exam_show(callback: CallbackQuery):
    _, group_code, group_name = callback.data.split(":", 2)
    await callback.message.edit_text(
        f"⏳ Завантажую розклад для *{group_name}*...",
        parse_mode="Markdown"
    )
    await callback.answer()

    schedule_text = get_exam_schedule(group_code)
    await callback.message.edit_text(schedule_text, parse_mode="Markdown")
