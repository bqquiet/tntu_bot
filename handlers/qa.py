import json
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
QA_FILE = "data/qa.json"


class QAStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer   = State()


# ─── JSON утиліти ────────────────────────────────────────────────────────────

def load_qa() -> list[dict]:
    if os.path.exists(QA_FILE):
        with open(QA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_qa(data: list[dict]):
    os.makedirs("data", exist_ok=True)
    with open(QA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_question(text: str) -> int:
    data = load_qa()
    new_id = max((q["id"] for q in data), default=0) + 1
    data.append({
        "id": new_id,
        "question": text,
        "answers": [],
        "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })
    save_qa(data)
    return new_id


def add_answer(question_id: int, text: str) -> bool:
    data = load_qa()
    for q in data:
        if q["id"] == question_id:
            q["answers"].append({
                "text": text,
                "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
            })
            save_qa(data)
            return True
    return False


# ─── Клавіатури ──────────────────────────────────────────────────────────────

def qa_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Задати питання анонімно", callback_data="qa_ask")],
        [InlineKeyboardButton(text="📋 Переглянути всі питання", callback_data="qa_list:0")],
    ])


def qa_list_keyboard(page: int, total: int, per_page: int = 5) -> InlineKeyboardMarkup:
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"qa_list:{page - 1}"))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton(text="Далі ▶️", callback_data=f"qa_list:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="❓ Задати питання", callback_data="qa_ask")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def answer_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Відповісти", callback_data=f"qa_answer:{question_id}")],
        [InlineKeyboardButton(text="◀️ До списку питань", callback_data="qa_list:0")],
    ])


# ─── Хендлери ────────────────────────────────────────────────────────────────

@router.message(F.text == "❓ Q&A")
async def qa_menu(message: Message, state: FSMContext):
    await state.clear()
    questions = load_qa()
    count = len(questions)
    unanswered = sum(1 for q in questions if not q["answers"])

    await message.answer(
        f"❓ *Анонімний Q&A*\n\n"
        f"Всього питань: *{count}*\n"
        f"Без відповіді: *{unanswered}*\n\n"
        "Тут можна анонімно задати питання або відповісти на чужі. "
        "Ніхто не знає хто питав — тільки текст питання.",
        reply_markup=qa_main_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "qa_ask")
async def qa_ask_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QAStates.waiting_for_question)
    await callback.message.answer(
        "❓ *Анонімне питання*\n\n"
        "Напиши своє питання — воно буде опубліковано анонімно.\n"
        "Ніхто не дізнається що питав саме ти.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(QAStates.waiting_for_question)
async def qa_save_question(message: Message, state: FSMContext):
    await state.clear()
    text = message.text.strip()

    if len(text) < 5:
        await message.answer("❌ Питання занадто коротке.")
        return
    if len(text) > 500:
        await message.answer("❌ Питання занадто довге (макс. 500 символів).")
        return

    q_id = add_question(text)
    await message.answer(
        f"✅ Питання *#{q_id}* опубліковано анонімно!\n\n"
        f"_\"{text}\"_\n\n"
        "Будь-хто може відповісти через розділ Q&A.",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("qa_list:"))
async def qa_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    page = int(callback.data.split(":")[1])
    per_page = 5
    questions = load_qa()

    if not questions:
        await callback.message.edit_text(
            "📋 Питань ще немає. Будь першим!",
            reply_markup=qa_main_keyboard()
        )
        await callback.answer()
        return

    # Сортуємо — спочатку без відповіді
    sorted_q = sorted(questions, key=lambda q: (len(q["answers"]) > 0, -q["id"]))
    start = page * per_page
    page_items = sorted_q[start:start + per_page]

    lines = [f"📋 *Питання ({start + 1}–{min(start + per_page, len(questions))} з {len(questions)}):*\n"]
    buttons = []

    for q in page_items:
        ans_count = len(q["answers"])
        status = f"💬 {ans_count}" if ans_count else "⏳ без відповіді"
        lines.append(f"*#{q['id']}* {status}\n_{q['question'][:80]}{'...' if len(q['question']) > 80 else ''}_")
        buttons.append([InlineKeyboardButton(
            text=f"#{q['id']} — {q['question'][:30]}...",
            callback_data=f"qa_view:{q['id']}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"qa_list:{page - 1}"))
    if (page + 1) * per_page < len(questions):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"qa_list:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="❓ Задати питання", callback_data="qa_ask")])

    await callback.message.edit_text(
        "\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("qa_view:"))
async def qa_view(callback: CallbackQuery):
    q_id = int(callback.data.split(":")[1])
    questions = load_qa()
    q = next((x for x in questions if x["id"] == q_id), None)

    if not q:
        await callback.answer("❌ Питання не знайдено")
        return

    lines = [f"❓ *Питання #{q['id']}*\n\n_{q['question']}_\n📅 {q['created']}\n"]

    if q["answers"]:
        lines.append(f"💬 *Відповіді ({len(q['answers'])}):\n*")
        for i, a in enumerate(q["answers"], 1):
            lines.append(f"*{i}.* {a['text']}\n_📅 {a['created']}_")
    else:
        lines.append("_Відповідей ще немає. Будь першим!_")

    await callback.message.edit_text(
        "\n\n".join(lines),
        reply_markup=answer_keyboard(q_id),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("qa_answer:"))
async def qa_answer_start(callback: CallbackQuery, state: FSMContext):
    q_id = int(callback.data.split(":")[1])
    await state.update_data(answering_id=q_id)
    await state.set_state(QAStates.waiting_for_answer)
    await callback.message.answer(
        f"💬 Відповідь на питання *#{q_id}*\n\nНапиши відповідь:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(QAStates.waiting_for_answer)
async def qa_save_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    q_id = data.get("answering_id")
    await state.clear()

    text = message.text.strip()
    if len(text) < 2:
        await message.answer("❌ Відповідь занадто коротка.")
        return

    success = add_answer(q_id, text)
    if success:
        await message.answer(
            f"✅ Відповідь на питання *#{q_id}* додано!",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Питання не знайдено.")