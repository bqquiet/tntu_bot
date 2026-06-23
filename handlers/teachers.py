import json
import os
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
TEACHERS_FILE = "data/teachers.json"
FACULTIES_LIST = ["ФІС", "ФПТ", "ФМТ", "ФЕМ"]


class TeacherStates(StatesGroup):
    waiting_for_query = State()


# ─── Дані ───────────────────────────────────────────────────────────────────

def load_teachers() -> list[dict]:
    if not os.path.exists(TEACHERS_FILE):
        return []
    with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def search_teachers(query: str, faculty_filter: str = "") -> list[dict]:
    teachers = load_teachers()
    q = query.lower().strip()
    results = []
    for t in teachers:
        if faculty_filter and t.get("faculty", "") != faculty_filter:
            continue
        haystack = " ".join([
            t.get("name", ""),
            t.get("position", ""),
            t.get("department", ""),
            " ".join(t.get("courses", [])),
        ]).lower()
        if q in haystack:
            results.append(t)
    return results


def format_teacher(t: dict) -> str:
    lines = [f"👨‍🏫 {t['name']}"]
    if t.get("position"):
        lines.append(f"📌 {t['position']}")
    lines.append(f"🏛 {t['department']} ({t.get('faculty','')})")
    if t.get("email"):
        lines.append(f"📧 {t['email']}")
    if t.get("courses"):
        lines.append(f"📚 {', '.join(t['courses'])}")
    if t.get("consultation"):
        lines.append(f"🕐 Консультації: {t['consultation']}")
    return "\n".join(lines)


def teacher_keyboard(t: dict) -> InlineKeyboardMarkup:
    """Кнопки для конкретного викладача."""
    buttons = []
    if t.get("schedule_url"):
        buttons.append([InlineKeyboardButton(
            text="📅 Розклад викладача",
            url=t["schedule_url"]
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


# ─── Клавіатури ─────────────────────────────────────────────────────────────

def faculty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f, callback_data=f"tf:{f}") for f in FACULTIES_LIST[:2]],
        [InlineKeyboardButton(text=f, callback_data=f"tf:{f}") for f in FACULTIES_LIST[2:]],
        [InlineKeyboardButton(text="🔍 Пошук по всьому університету", callback_data="tf:all")],
    ])


def dept_keyboard(faculty: str) -> tuple[InlineKeyboardMarkup, list[str]]:
    teachers = load_teachers()
    depts = sorted(set(
        t["department"] for t in teachers
        if t.get("faculty") == faculty
    ))
    buttons = [
        [InlineKeyboardButton(text=d[:38], callback_data=f"tdept:{faculty}:{i}")]
        for i, d in enumerate(depts)
    ]
    buttons.append([InlineKeyboardButton(text="🔍 Пошук по імені/дисципліні", callback_data=f"tf:{faculty}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="tf:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons), depts


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "👨‍🏫 Викладачі")
async def teacher_menu(message: Message, state: FSMContext):
    await state.clear()
    total = len(load_teachers())
    await message.answer(
        f"👨‍🏫 Викладачі ТНТУ\n\n"
        f"В базі: {total} викладачів з усіх факультетів\n\n"
        "Оберіть факультет або скористайтеся пошуком:",
        reply_markup=faculty_keyboard()
    )


@router.callback_query(F.data == "tf:back")
async def back_to_faculty(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    total = len(load_teachers())
    await callback.message.edit_text(
        f"👨‍🏫 Викладачі ТНТУ\n\nВ базі: {total} викладачів\n\nОберіть факультет:",
        reply_markup=faculty_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tf:"))
async def faculty_chosen(callback: CallbackQuery, state: FSMContext):
    faculty = callback.data.split(":", 1)[1]

    if faculty == "all":
        await state.update_data(faculty_filter="")
        await state.set_state(TeacherStates.waiting_for_query)
        await callback.message.edit_text(
            "🔍 Пошук по всьому університету\n\n"
            "Введи прізвище, ім'я, назву кафедри або дисципліну:"
        )
        await callback.answer()
        return

    kb, depts = dept_keyboard(faculty)
    count = sum(1 for t in load_teachers() if t.get("faculty") == faculty)
    await callback.message.edit_text(
        f"👨‍🏫 {faculty} — {count} викладачів\n\n"
        "Оберіть кафедру або скористайтеся пошуком:",
        reply_markup=kb
    )
    await state.update_data(faculty_filter=faculty, depts=depts)
    await callback.answer()


@router.callback_query(F.data.startswith("tdept:"))
async def dept_chosen(callback: CallbackQuery, state: FSMContext):
    _, faculty, idx_str = callback.data.split(":", 2)
    data = await state.get_data()
    depts = data.get("depts", [])
    idx = int(idx_str)

    if idx >= len(depts):
        await callback.answer("❌ Помилка")
        return

    dept_name = depts[idx]
    teachers = [t for t in load_teachers() if t.get("department") == dept_name]

    if not teachers:
        await callback.answer("Викладачів не знайдено")
        return

    await callback.answer()

    # Відправляємо кожного викладача окремим повідомленням з кнопкою розкладу
    header = f"🏛 {dept_name}\nВикладачів: {len(teachers)}\n"
    await callback.message.edit_text(header)

    for t in teachers:
        kb = teacher_keyboard(t)
        try:
            if kb:
                await callback.message.answer(format_teacher(t), reply_markup=kb)
            else:
                await callback.message.answer(format_teacher(t))
        except Exception:
            pass


@router.message(TeacherStates.waiting_for_query)
async def teacher_search_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    faculty_filter = data.get("faculty_filter", "")
    await state.clear()

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("❌ Запит занадто короткий. Введи хоча б 2 символи.")
        return

    results = search_teachers(query, faculty_filter)

    if not results:
        hint = f" на факультеті {faculty_filter}" if faculty_filter else ""
        await message.answer(
            f"Нічого не знайдено за запитом \"{query}\"{hint}.\n"
            "Спробуй інше прізвище або назву дисципліни."
        )
        return

    await message.answer(f"Знайдено {len(results)} результатів за запитом \"{query}\":")

    for t in results[:5]:
        kb = teacher_keyboard(t)
        if kb:
            await message.answer(format_teacher(t), reply_markup=kb)
        else:
            await message.answer(format_teacher(t))

    if len(results) > 5:
        await message.answer(f"...і ще {len(results) - 5}. Уточни запит для точнішого результату.")