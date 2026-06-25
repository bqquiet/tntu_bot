import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import FACULTIES, TNTU_BASE_URL
from scrapers.schedule_scraper import get_faculty_data, get_exam_schedule, get_schedule_pdfs

router = Router()
USERS_FILE = "data/users.json"


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
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"sc_fac:{mode}:{code}")]
        for name, code in FACULTIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_keyboard(mode: str, faculty_code: str, courses: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=c, callback_data=f"sc_course:{mode}:{faculty_code}:{c}")]
        for c in courses
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"sc_back:fac:{mode}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def group_keyboard(mode: str, faculty_code: str, course: str, groups: list) -> InlineKeyboardMarkup:
    buttons, row = [], []
    for name, code in groups:
        row.append(InlineKeyboardButton(
            text=name,
            callback_data=f"sc_grp:{mode}:{faculty_code}:{course}:{code}:{name}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"sc_course:{mode}:{faculty_code}:{course}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def saved_group_keyboard(mode: str, group: dict) -> InlineKeyboardMarkup:
    label = "📅 Розклад занять" if mode == "pdf" else "📝 Екзамени"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"📌 Моя група: {group['group_name']}",
            callback_data=f"sc_show:{mode}:{group['faculty']}:{group['group_code']}:{group['group_name']}"
        )],
        [InlineKeyboardButton(text="🔍 Інша група", callback_data=f"sc_back:fac:{mode}")],
    ])


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "📅 Розклад занять")
async def schedule_menu(message: Message):
    saved = get_user_group(message.from_user.id)
    if saved:
        await message.answer(
            "📅 Розклад занять\n\nОберіть групу:",
            reply_markup=saved_group_keyboard("pdf", saved)
        )
    else:
        await message.answer(
            "📅 Розклад занять\n\nОберіть факультет:",
            reply_markup=faculty_keyboard("pdf")
        )


@router.message(F.text == "📝 Розклад екзаменів")
async def exams_menu(message: Message):
    saved = get_user_group(message.from_user.id)
    if saved:
        await message.answer(
            "📝 Розклад екзаменів\n\nОберіть групу:",
            reply_markup=saved_group_keyboard("exam", saved)
        )
    else:
        await message.answer(
            "📝 Розклад екзаменів\n\nОберіть факультет:",
            reply_markup=faculty_keyboard("exam")
        )


@router.callback_query(F.data.startswith("sc_back:fac:"))
async def back_to_faculty(callback: CallbackQuery):
    mode = callback.data.split(":")[-1]
    title = "📅 Розклад занять" if mode == "pdf" else "📝 Розклад екзаменів"
    await callback.message.edit_text(
        f"{title}\n\nОберіть факультет:",
        reply_markup=faculty_keyboard(mode)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sc_fac:"))
async def faculty_chosen(callback: CallbackQuery):
    _, mode, faculty_code = callback.data.split(":", 2)
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code.upper())

    await callback.message.edit_text(f"⏳ Завантажую групи {faculty_name}...")
    await callback.answer()

    data = get_faculty_data(faculty_code)
    groups_by_course = data.get("groups_by_course", {})

    if not groups_by_course:
        await callback.message.edit_text(
            f"❌ Не вдалося завантажити групи {faculty_name}.\n\n"
            f"🔗 {TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
        )
        return

    courses = list(groups_by_course.keys())
    await callback.message.edit_text(
        f"📚 {faculty_name}\n\nОберіть курс:",
        reply_markup=course_keyboard(mode, faculty_code, courses)
    )


@router.callback_query(F.data.startswith("sc_course:"))
async def course_chosen(callback: CallbackQuery):
    parts = callback.data.split(":", 3)
    _, mode, faculty_code, course = parts
    faculty_name = next((k for k, v in FACULTIES.items() if v == faculty_code), faculty_code.upper())

    data = get_faculty_data(faculty_code)
    groups = data.get("groups_by_course", {}).get(course, [])

    if not groups:
        await callback.message.edit_text(
            f"❌ Групи для {course} не знайдено.\n"
            f"🔗 {TNTU_BASE_URL}/?p=uk/schedule&s={faculty_code}"
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📚 {faculty_name} — {course}\n\nОберіть групу:",
        reply_markup=group_keyboard(mode, faculty_code, course, groups)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sc_grp:"))
async def group_chosen(callback: CallbackQuery):
    # sc_grp:mode:faculty:course:code:name
    parts = callback.data.split(":")
    mode         = parts[1]
    faculty_code = parts[2]
    course       = parts[3]
    group_code   = parts[4]
    group_name   = parts[5]

    save_user_group(callback.from_user.id, faculty_code, group_name, group_code)
    await callback.message.edit_text(f"⏳ Завантажую для групи {group_name}...")
    await callback.answer()

    await _show_schedule(callback.message, mode, faculty_code, group_code, group_name)


@router.callback_query(F.data.startswith("sc_show:"))
async def show_saved(callback: CallbackQuery):
    # sc_show:mode:faculty:code:name
    parts = callback.data.split(":", 4)
    mode, faculty_code, group_code, group_name = parts[1], parts[2], parts[3], parts[4]

    await callback.message.edit_text(f"⏳ Завантажую для групи {group_name}...")
    await callback.answer()

    await _show_schedule(callback.message, mode, faculty_code, group_code, group_name)


async def _show_schedule(message, mode: str, faculty_code: str, group_code: str, group_name: str):
    if mode == "exam":
        text = get_exam_schedule(group_code, group_name)
    else:
        text = get_schedule_pdfs(faculty_code, group_name)

    # Розбиваємо якщо > 4000 символів
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    await message.edit_text(chunks[0], disable_web_page_preview=True)
    for chunk in chunks[1:]:
        await message.answer(chunk, disable_web_page_preview=True)