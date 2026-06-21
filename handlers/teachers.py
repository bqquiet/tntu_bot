import json
import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

TEACHERS_FILE = "data/teachers.json"


class TeacherStates(StatesGroup):
    waiting_for_query = State()


def load_teachers() -> list[dict]:
    if not os.path.exists(TEACHERS_FILE):
        return []
    with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def search_teachers(query: str) -> list[dict]:
    """Шукає викладача по імені, кафедрі або дисципліні."""
    teachers = load_teachers()
    query_lower = query.lower().strip()

    results = []
    for t in teachers:
        # Перевіряємо ім'я, скорочення, кафедру і курси
        searchable = " ".join([
            t.get("name", ""),
            t.get("short", ""),
            t.get("department", ""),
            " ".join(t.get("courses", [])),
        ]).lower()

        if query_lower in searchable:
            results.append(t)

    return results


def format_teacher(t: dict) -> str:
    lines = [f"👨‍🏫 *{t['name']}*"]
    lines.append(f"📌 {t['position']}")
    lines.append(f"🏛 {t['department']}")

    if t.get("email"):
        lines.append(f"📧 {t['email']}")

    if t.get("courses"):
        courses_str = ", ".join(t["courses"])
        lines.append(f"📚 Дисципліни: {courses_str}")

    return "\n".join(lines)


@router.message(F.text == "👨‍🏫 Викладачі")
async def teacher_menu(message: Message, state: FSMContext):
    await state.set_state(TeacherStates.waiting_for_query)
    await message.answer(
        "👨‍🏫 *Пошук викладача*\n\n"
        "Введи ім'я, прізвище, назву кафедри або дисципліну:\n"
        "_Наприклад: Осухівська, програмування, СА_",
        parse_mode="Markdown"
    )


@router.message(TeacherStates.waiting_for_query)
async def teacher_search(message: Message, state: FSMContext):
    await state.clear()
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❌ Запит занадто короткий. Введи хоча б 2 символи.")
        return

    results = search_teachers(query)

    if not results:
        await message.answer(
            f"🔍 За запитом *\"{query}\"* нічого не знайдено.\n\n"
            "Спробуй інше ім'я або назву дисципліни.",
            parse_mode="Markdown"
        )
        return

    if len(results) == 1:
        await message.answer(format_teacher(results[0]), parse_mode="Markdown")
        return

    # Кілька результатів
    header = f"🔍 Знайдено *{len(results)}* викладачів за запитом \"{query}\":\n"
    cards = [format_teacher(t) for t in results[:5]]  # максимум 5
    text = header + "\n\n─────────────────\n\n".join(cards)

    if len(results) > 5:
        text += f"\n\n_...і ще {len(results) - 5}. Уточни запит для точнішого результату._"

    await message.answer(text, parse_mode="Markdown")