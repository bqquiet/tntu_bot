import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import FACULTIES, TNTU_BASE_URL
from scrapers.schedule_scraper import get_faculty_data, get_exam_schedule, get_schedule_pdfs

router = Router()
USERS_FILE = "data/users.json"


# ─── Збереження групи користувача ────────────────────────────────────────────

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
    return load_users().get(str(user_id))


# ─── Клавіатури ──────────────────────────────────────────────────────────────

def faculty_keyboard(mode: str) -> InlineKeyboardMarkup:
    """mode: 'exam' або 'pdf'"""
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"fac:{mode}:{code}")]
        for name, code in FACULTIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_keyboard(mode: str, faculty_code: str, groups_by_course: dict) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=course,
            callback_data=f"course:{mode}:{faculty_code}:{course}"
        )]
        for course in groups_by_course
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"back:fac:{mode}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def group_keyboard(mode: str, faculty_code: str, course: str, group_list: list) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for name, code in group_list:
        row.append(InlineKeyboardButton(
            text=name,
            callback_data=f"grp:{mode}:{faculty_code}:{code}:{name}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"course:{mode}:{faculty_code}:{course}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери — Розклад занять ───────────────────────────────────────────────

@router.message(F.text == "📅 Розклад занять")
async def schedule_menu(message: Message):
    user_group = get_user_group(message.from_user.id)
    if user_group:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"📌 Моя група: {user_group['group_name']}",
                callback_data=f"grp:pdf:{user_group['faculty']}:{user_group['group_code']}:{user_group['group_name']}"
            )],
            [InlineKeyboardButton(text="🔍 Інша група", callback_data="back:fac:pdf")],
        ])
        await message.answer("📅 Розклад занять\n\nОберіть групу:", reply_markup=kb)
    else:
        await message.answer(
            "📅 Розклад занять\n\nОберіть факультет:",
            reply_markup=faculty_keyboard("pdf")
        )


# ─── Хендлери — Розклад екзаменів ────────────────────────────────────────────

@router.message(F.text == "📝 Розклад екзаменів")
async def exams_menu(message: Message):
    user_group = get_user_group(message.from_user.id)
    if user_group:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"📌 Моя група: {user_group['group_name']}",
                callback_data=f"grp:exam:{user_group['faculty']}:{user_group['group_code']}:{user_group['group_name']}"
            )],
            [InlineKeyboardButton(text="🔍 Інша група", callback_data="back:fac:exam")],
        ])
        await message.answer("📝 Розклад екзаменів\n\nОберіть групу:", reply_markup=kb)
    else:
        await message.answer(
            "📝 Розклад екзаменів\n\nОберіть факультет:",
            reply_markup=faculty_keyboard("exam")
        )


# ─── Спільні callback хендлери ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("back:fac:"))
async def back_to_faculty(callback: CallbackQuery):
    mode = callback.data.split(":")[2]
    title = "📅 Розклад занять" if mode == "pdf" else "📝 Розклад екзаменів"
    await callback.message.edit_text(
        f"{title}\n\nОберіть факультет:",
        reply_markup=faculty_keyboard(mode)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fac:"))
async def faculty_chosen(callback: CallbackQuery):
    _, mode, faculty_code = callback.data.split(":", 2)
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code.upper())

    msg = await callback.message.edit_text(f"⏳ Завантажую список груп {faculty_name}...")
    await callback.answer()

    data = get_faculty_data(faculty_code)
    groups_by_course = data["groups_by_course"]

    if not groups_by_course:
        await msg.edit_text(
            f"❌ Не вдалося завантажити групи {faculty_name}.\n"
            f"🔗 {TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
        )
        return

    await msg.edit_text(
        f"📚 {faculty_name}\n\nОберіть курс:",
        reply_markup=course_keyboard(mode, faculty_code, groups_by_course)
    )


@router.callback_query(F.data.startswith("course:"))
async def course_chosen(callback: CallbackQuery):
    parts = callback.data.split(":", 3)
    mode, faculty_code, course = parts[1], parts[2], parts[3]
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code.upper())

    data = get_faculty_data(faculty_code)
    group_list = data["groups_by_course"].get(course, [])

    await callback.message.edit_text(
        f"📚 {faculty_name} — {course}\n\nОберіть групу:",
        reply_markup=group_keyboard(mode, faculty_code, course, group_list)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("grp:"))
async def group_chosen(callback: CallbackQuery):
    parts = callback.data.split(":")
    mode        = parts[1]
    faculty_code = parts[2]
    group_code  = parts[3]
    group_name  = parts[4]

    save_user_group(callback.from_user.id, faculty_code, group_name, group_code)

    await callback.message.edit_text(f"⏳ Завантажую для групи {group_name}...")
    await callback.answer()

    if mode == "exam":
        text = get_exam_schedule(group_code)
    else:
        text = get_schedule_pdfs(faculty_code, group_name)

    # Telegram має ліміт 4096 символів — розбиваємо якщо треба
    if len(text) > 4000:
        parts_text = [text[i:i+4000] for i in range(0, len(text), 4000)]
        await callback.message.edit_text(parts_text[0])
        for part in parts_text[1:]:
            await callback.message.answer(part)
    else:
        await callback.message.edit_text(text)