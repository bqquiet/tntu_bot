import json
import os
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

TEACHERS_FILE = "data/teachers.json"
FACULTIES = ["ФІС", "ФПТ", "ФМТ", "ФЕМ"]


class TeacherStates(StatesGroup):
    waiting_for_query = State()


def load_teachers() -> list[dict]:
    if not os.path.exists(TEACHERS_FILE):
        return []
    with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def search_teachers(query: str, faculty_filter: str = "") -> list[dict]:
    teachers = load_teachers()
    query_lower = query.lower().strip()
    results = []
    for t in teachers:
        if faculty_filter and t.get("faculty", "") != faculty_filter:
            continue
        searchable = " ".join([
            t.get("name", ""),
            t.get("position", ""),
            t.get("department", ""),
            " ".join(t.get("courses", [])),
        ]).lower()
        if query_lower in searchable:
            results.append(t)
    return results


def format_teacher(t: dict) -> str:
    lines = [f"👨‍🏫 *{t['name']}*"]
    if t.get("position"):
        lines.append(f"📌 {t['position']}")
    lines.append(f"🏛 {t['department']} · {t.get('faculty','')}")
    if t.get("email"):
        lines.append(f"📧 {t['email']}")
    if t.get("courses"):
        lines.append(f"📚 {', '.join(t['courses'])}")
    return "\n".join(lines)


def faculty_filter_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f, callback_data=f"tf:{f}") for f in FACULTIES],
        [InlineKeyboardButton(text="🔍 Всі факультети", callback_data="tf:all")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "👨‍🏫 Викладачі")
async def teacher_menu(message: Message, state: FSMContext):
    await state.clear()
    total = len(load_teachers())
    await message.answer(
        f"👨‍🏫 *Пошук викладача*\n\n"
        f"В базі: *{total}* викладачів з усіх факультетів\n\n"
        "Спочатку оберіть факультет або шукайте по всіх:",
        reply_markup=faculty_filter_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("tf:"))
async def faculty_filter_chosen(callback: CallbackQuery, state: FSMContext):
    faculty = callback.data.split(":", 1)[1]
    label = faculty if faculty != "all" else "всіх факультетів"
    await state.update_data(faculty_filter=faculty if faculty != "all" else "")
    await state.set_state(TeacherStates.waiting_for_query)
    await callback.message.edit_text(
        f"🔍 Пошук по *{label}*\n\n"
        "Введи прізвище, ім'я, назву кафедри або дисципліну:\n"
        "_Наприклад: Петрик, програмування, КН, фізика_",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(TeacherStates.waiting_for_query)
async def teacher_search(message: Message, state: FSMContext):
    data = await state.get_data()
    faculty_filter = data.get("faculty_filter", "")
    await state.clear()

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("❌ Запит занадто короткий. Введи хоча б 2 символи.")
        return

    results = search_teachers(query, faculty_filter)

    if not results:
        hint = f" на факультеті *{faculty_filter}*" if faculty_filter else ""
        await message.answer(
            f"🔍 За запитом *\"{query}\"*{hint} нічого не знайдено.\n\n"
            "Спробуй інше прізвище або назву дисципліни.",
            parse_mode="Markdown"
        )
        return

    if len(results) == 1:
        await message.answer(format_teacher(results[0]), parse_mode="Markdown")
        return

    header = f"🔍 Знайдено *{len(results)}* результатів за запитом \"{query}\":\n\n"
    cards = "\n\n─────────────\n\n".join(format_teacher(t) for t in results[:5])
    text = header + cards

    if len(results) > 5:
        text += f"\n\n_...і ще {len(results) - 5}. Уточни запит._"

    await message.answer(text, parse_mode="Markdown")