import json, os, random, asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/quiz.json"
LETTERS = ["A","B","C","D"]

class QZ(StatesGroup):
    subject = State()
    playing = State()

def load() -> list:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else []

def subjects() -> list[str]:
    return sorted(set(q["subject"] for q in load()))

def subj_kb() -> InlineKeyboardMarkup:
    subs = subjects()
    buttons = [[InlineKeyboardButton(text=f"📚 {s}", callback_data=f"qz_sub:{s}")] for s in subs]
    buttons.append([InlineKeyboardButton(text="🎲 Всі теми (перемішано)", callback_data="qz_sub:all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def ans_kb(qid: int, opts: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{LETTERS[i]}. {o[:40]}", callback_data=f"qz_ans:{qid}:{i}")]
        for i, o in enumerate(opts)
    ])

def fmt_q(q: dict, num: int, total: int) -> str:
    opts = "\n".join(f"  <b>{LETTERS[i]}.</b> {o}" for i,o in enumerate(q["options"]))
    return (
        f"🎯 <b>Вікторина</b> — питання {num}/{total}\n"
        f"<i>Тема: {q['subject']}</i>\n"
        f"{'─'*24}\n"
        f"<b>{q['question']}</b>\n\n{opts}"
    )

@router.message(F.text == "🎯 Вікторина")
async def quiz_menu(message: Message, state: FSMContext):
    await state.clear()
    total = len(load())
    await message.answer(
        f"🎯 <b>Вікторина</b>\n\n"
        f"Питань у базі: <b>{total}</b>\n"
        f"Теми: {', '.join(subjects())}\n\n"
        f"Оберіть тему або грайте з усіма:",
        parse_mode="HTML", reply_markup=subj_kb()
    )
    await state.set_state(QZ.subject)

@router.callback_query(F.data.startswith("qz_sub:"), QZ.subject)
async def quiz_start(cb: CallbackQuery, state: FSMContext):
    sub = cb.data.split(":",1)[1]
    all_q = load()
    pool = all_q if sub == "all" else [q for q in all_q if q["subject"] == sub]
    if not pool:
        await cb.answer("❌ Питань немає"); return
    chosen = random.sample(pool, min(10, len(pool)))
    await state.update_data(ids=[q["id"] for q in chosen], idx=0, score=0, sub=sub)
    await state.set_state(QZ.playing)
    q = chosen[0]
    await cb.message.edit_text(fmt_q(q, 1, len(chosen)),
                               parse_mode="HTML", reply_markup=ans_kb(q["id"], q["options"]))
    await cb.answer()

@router.callback_query(F.data.startswith("qz_ans:"), QZ.playing)
async def quiz_answer(cb: CallbackQuery, state: FSMContext):
    _, qid_s, chosen_s = cb.data.split(":")
    qid, chosen = int(qid_s), int(chosen_s)
    data = await state.get_data()
    ids, idx, score, sub = data["ids"], data["idx"], data["score"], data["sub"]
    all_q = load()
    q = next((x for x in all_q if x["id"] == qid), None)
    if not q:
        await cb.answer("❌"); return
    correct = q["answer"]
    is_ok = chosen == correct
    if is_ok: score += 1

    if is_ok:
        result = f"✅ <b>Правильно!</b>\n<i>{q['options'][correct]}</i>"
    else:
        result = (f"❌ <b>Неправильно</b>\n"
                  f"Твоя: <i>{q['options'][chosen]}</i>\n"
                  f"Вірна: <i>{q['options'][correct]}</i>")

    next_idx = idx + 1
    total = len(ids)
    await state.update_data(idx=next_idx, score=score)
    await cb.answer("✅ Вірно!" if is_ok else "❌ Невірно")

    if next_idx >= total:
        await state.clear()
        pct = round(score / total * 100)
        if pct == 100:   emoji, msg = "🏆", "Ідеальний результат!"
        elif pct >= 80:  emoji, msg = "🎉", "Чудово! Матеріал засвоєно добре."
        elif pct >= 50:  emoji, msg = "👍", "Непогано, але є над чим працювати."
        else:            emoji, msg = "📚", "Варто повторити матеріал."

        final_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ще раз", callback_data=f"qz_sub:{sub}")],
            [InlineKeyboardButton(text="📚 Інша тема", callback_data="qz_restart")],
        ])
        await cb.message.edit_text(
            f"{result}\n\n{'─'*24}\n"
            f"{emoji} <b>Вікторину завершено!</b>\n\n"
            f"Правильних: <b>{score}/{total}</b>\n"
            f"Результат:  <b>{pct}%</b>\n\n{msg}",
            parse_mode="HTML", reply_markup=final_kb
        )
        return

    await cb.message.edit_text(
        f"{result}\n\n<i>Рахунок: {score}/{next_idx}</i>",
        parse_mode="HTML"
    )
    await asyncio.sleep(1.5)
    next_q = next((x for x in all_q if x["id"] == ids[next_idx]), None)
    if next_q:
        await cb.message.edit_text(
            fmt_q(next_q, next_idx+1, total),
            parse_mode="HTML",
            reply_markup=ans_kb(next_q["id"], next_q["options"])
        )

@router.callback_query(F.data == "qz_restart")
async def quiz_restart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QZ.subject)
    await cb.message.edit_text(
        "🎯 <b>Вікторина</b>\n\nОберіть тему:",
        parse_mode="HTML", reply_markup=subj_kb()
    )
    await cb.answer()