import json
import random
import os
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
QUIZ_FILE = "data/quiz.json"

LETTERS = ["A", "B", "C", "D"]


class QuizStates(StatesGroup):
    choosing_subject = State()
    in_progress      = State()


# ─── Утиліти ─────────────────────────────────────────────────────────────────

def load_questions() -> list[dict]:
    if not os.path.exists(QUIZ_FILE):
        return []
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_subjects() -> list[str]:
    questions = load_questions()
    return sorted(set(q["subject"] for q in questions))


def get_questions_by_subject(subject: str) -> list[dict]:
    questions = load_questions()
    if subject == "all":
        return questions
    return [q for q in questions if q["subject"] == subject]


def format_question(q: dict, num: int, total: int) -> str:
    lines = [f"🎯 *Вікторина — питання {num}/{total}*\n"]
    lines.append(f"📚 Тема: _{q['subject']}_\n")
    lines.append(f"*{q['question']}*\n")
    for i, option in enumerate(q["options"]):
        lines.append(f"{LETTERS[i]}. {option}")
    return "\n".join(lines)


def answer_keyboard(q_id: int, options: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{LETTERS[i]}. {opt[:30]}",
            callback_data=f"quiz_ans:{q_id}:{i}"
        )]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subject_keyboard() -> InlineKeyboardMarkup:
    subjects = get_subjects()
    buttons = [
        [InlineKeyboardButton(text=f"📚 {s}", callback_data=f"quiz_sub:{s}")]
        for s in subjects
    ]
    buttons.append([InlineKeyboardButton(text="🎲 Всі теми перемішано", callback_data="quiz_sub:all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "🎯 Вікторина")
async def quiz_menu(message: Message, state: FSMContext):
    await state.clear()
    total = len(load_questions())
    subjects = get_subjects()

    await message.answer(
        f"🎯 *Вікторина*\n\n"
        f"Всього питань у базі: *{total}*\n"
        f"Теми: {', '.join(subjects)}\n\n"
        "Обери тему або грай з усіма питаннями перемішано:",
        reply_markup=subject_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(QuizStates.choosing_subject)


@router.callback_query(F.data.startswith("quiz_sub:"), QuizStates.choosing_subject)
async def quiz_start(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split(":", 1)[1]
    questions = get_questions_by_subject(subject)

    if not questions:
        await callback.answer("❌ Питань за цією темою немає")
        return

    # Перемішуємо і беремо до 10 питань
    shuffled = random.sample(questions, min(10, len(questions)))

    await state.update_data(
        questions=[q["id"] for q in shuffled],
        current=0,
        score=0,
        subject=subject,
    )
    await state.set_state(QuizStates.in_progress)

    # Показуємо перше питання
    q = shuffled[0]
    await callback.message.edit_text(
        format_question(q, 1, len(shuffled)),
        reply_markup=answer_keyboard(q["id"], q["options"]),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz_ans:"), QuizStates.in_progress)
async def quiz_answer(callback: CallbackQuery, state: FSMContext):
    _, q_id_str, chosen_str = callback.data.split(":")
    q_id = int(q_id_str)
    chosen = int(chosen_str)

    data = await state.get_data()
    questions_ids = data["questions"]
    current = data["current"]
    score = data["score"]

    # Знаходимо питання
    all_q = load_questions()
    q = next((x for x in all_q if x["id"] == q_id), None)
    if not q:
        await callback.answer("❌ Помилка")
        return

    correct = q["answer"]
    is_correct = chosen == correct

    if is_correct:
        score += 1
        result_text = f"✅ *Правильно!*\n_{q['options'][correct]}_"
    else:
        result_text = (
            f"❌ *Неправильно.*\n"
            f"Твоя відповідь: _{q['options'][chosen]}_\n"
            f"Правильна: _{q['options'][correct]}_"
        )

    next_index = current + 1
    total = len(questions_ids)

    await state.update_data(current=next_index, score=score)

    if next_index >= total:
        # Вікторина завершена
        await state.clear()
        percent = round(score / total * 100)
        emoji = "🏆" if percent >= 80 else ("👍" if percent >= 50 else "📚")

        final = (
            f"{result_text}\n\n"
            f"─────────────────\n"
            f"{emoji} *Вікторина завершена!*\n\n"
            f"Правильних відповідей: *{score}/{total}*\n"
            f"Результат: *{percent}%*\n\n"
        )

        if percent == 100:
            final += "🌟 Ідеальний результат! Ти відмінно знаєш матеріал!"
        elif percent >= 80:
            final += "🎉 Чудовий результат! Матеріал засвоєно добре."
        elif percent >= 50:
            final += "👍 Непогано, але є над чим попрацювати."
        else:
            final += "📚 Варто повторити матеріал. Не здавайся!"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Пройти ще раз", callback_data=f"quiz_sub:{data['subject']}")],
            [InlineKeyboardButton(text="📚 Інша тема", callback_data="quiz_restart")],
        ])

        await callback.message.edit_text(final, reply_markup=kb, parse_mode="Markdown")
        await callback.answer("Вікторину завершено!" if is_correct else "Неправильно 😔")
        return

    # Показуємо результат поточного питання і одразу наступне
    next_q_id = questions_ids[next_index]
    next_q = next((x for x in all_q if x["id"] == next_q_id), None)

    # Спочатку показуємо результат
    await callback.message.edit_text(
        f"{result_text}\n\n_Рахунок: {score}/{next_index} ✅_",
        parse_mode="Markdown"
    )
    await callback.answer("✅ Вірно!" if is_correct else "❌ Невірно")

    # Потім наступне питання
    import asyncio
    await asyncio.sleep(1.5)

    await callback.message.edit_text(
        format_question(next_q, next_index + 1, total),
        reply_markup=answer_keyboard(next_q["id"], next_q["options"]),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "quiz_restart")
async def quiz_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizStates.choosing_subject)
    await callback.message.edit_text(
        "🎯 *Вікторина*\n\nОбери тему:",
        reply_markup=subject_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()