import json, os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
FILE = "data/qa.json"

class QAS(StatesGroup):
    question = State()
    answer   = State()

def load() -> list:
    return json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else []

def save(d: list):
    os.makedirs("data", exist_ok=True)
    json.dump(d, open(FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Задати питання анонімно", callback_data="qa_ask")],
        [InlineKeyboardButton(text="📋 Переглянути всі питання", callback_data="qa_list:0")],
    ])

def list_kb(page: int, total: int, per=5) -> InlineKeyboardMarkup:
    qs = load()
    sorted_q = sorted(qs, key=lambda q: (len(q["answers"])>0, -q["id"]))
    start = page * per
    items = sorted_q[start:start+per]
    buttons = [
        [InlineKeyboardButton(
            text=f"#{q['id']} {'💬' if q['answers'] else '⏳'} {q['question'][:35]}...",
            callback_data=f"qa_view:{q['id']}"
        )] for q in items
    ]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"qa_list:{page-1}"))
    if (page+1)*per < total:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"qa_list:{page+1}"))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="❓ Задати питання", callback_data="qa_ask")])
    buttons.append([InlineKeyboardButton(text="◀️ Головна Q&A", callback_data="qa_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def answer_kb(qid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Відповісти", callback_data=f"qa_answer:{qid}")],
        [InlineKeyboardButton(text="◀️ До списку", callback_data="qa_list:0")],
    ])

@router.message(F.text == "❓ Q&A")
async def qa_menu(message: Message, state: FSMContext):
    await state.clear()
    qs = load()
    unanswered = sum(1 for q in qs if not q["answers"])
    await message.answer(
        f"❓ <b>Анонімний Q&A</b>\n\n"
        f"Питань всього: <b>{len(qs)}</b>\n"
        f"Без відповіді: <b>{unanswered}</b>\n\n"
        f"Тут можна анонімно задати питання або відповісти на чуже.\n"
        f"<i>Ніхто не побачить хто питав.</i>",
        parse_mode="HTML", reply_markup=main_kb()
    )

@router.callback_query(F.data == "qa_main")
async def qa_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    qs = load()
    unanswered = sum(1 for q in qs if not q["answers"])
    await cb.message.edit_text(
        f"❓ <b>Анонімний Q&A</b>\n\nПитань: <b>{len(qs)}</b> | Без відповіді: <b>{unanswered}</b>",
        parse_mode="HTML", reply_markup=main_kb()
    )
    await cb.answer()

@router.callback_query(F.data == "qa_ask")
async def qa_ask(cb: CallbackQuery, state: FSMContext):
    await state.set_state(QAS.question)
    await cb.message.answer(
        "❓ <b>Анонімне питання</b>\n\nНапиши своє питання — його опублікують анонімно:",
        parse_mode="HTML"
    )
    await cb.answer()

@router.message(QAS.question)
async def qa_save_q(message: Message, state: FSMContext):
    await state.clear()
    t = message.text.strip()
    if len(t) < 5:
        await message.answer("❌ Питання занадто коротке.")
        return
    qs = load()
    nid = max((q["id"] for q in qs), default=0) + 1
    qs.append({"id":nid,"question":t,"answers":[],
               "created":datetime.now().strftime("%d.%m.%Y %H:%M")})
    save(qs)
    await message.answer(
        f"✅ <b>Питання #{nid} опубліковано!</b>\n\n<i>{t}</i>\n\n"
        f"Будь-хто може відповісти анонімно.",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("qa_list:"))
async def qa_list(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    page = int(cb.data.split(":")[1])
    qs = load()
    if not qs:
        await cb.message.edit_text(
            "📋 Питань ще немає. Будь першим!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❓ Задати питання", callback_data="qa_ask")]
            ])
        )
        await cb.answer(); return
    sorted_q = sorted(qs, key=lambda q: (len(q["answers"])>0, -q["id"]))
    per = 5
    total = len(sorted_q)
    start = page * per
    page_items = sorted_q[start:start+per]
    lines = [f"📋 <b>Питання ({start+1}–{min(start+per,total)} з {total})</b>\n"]
    for q in page_items:
        ans = len(q["answers"])
        status = f"💬 {ans} відп." if ans else "⏳ без відповіді"
        lines.append(f"<b>#{q['id']}</b> [{status}]\n<i>{q['question'][:80]}</i>")
    await cb.message.edit_text(
        "\n\n".join(lines),
        parse_mode="HTML",
        reply_markup=list_kb(page, total, per)
    )
    await cb.answer()

@router.callback_query(F.data.startswith("qa_view:"))
async def qa_view(cb: CallbackQuery):
    qid = int(cb.data.split(":")[1])
    qs = load()
    q = next((x for x in qs if x["id"] == qid), None)
    if not q:
        await cb.answer("❌ Не знайдено"); return
    lines = [
        f"❓ <b>Питання #{q['id']}</b>\n",
        f"<i>{q['question']}</i>",
        f"<i>📅 {q['created']}</i>",
    ]
    if q["answers"]:
        lines.append(f"\n💬 <b>Відповіді ({len(q['answers'])}):</b>")
        for i, a in enumerate(q["answers"], 1):
            lines.append(f"\n<b>{i}.</b> {a['text']}\n<i>📅 {a['created']}</i>")
    else:
        lines.append("\n<i>Відповідей ще немає. Будь першим!</i>")
    await cb.message.edit_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=answer_kb(qid)
    )
    await cb.answer()

@router.callback_query(F.data.startswith("qa_answer:"))
async def qa_answer_start(cb: CallbackQuery, state: FSMContext):
    qid = int(cb.data.split(":")[1])
    await state.update_data(qid=qid)
    await state.set_state(QAS.answer)
    await cb.message.answer(
        f"💬 Відповідь на питання <b>#{qid}</b>\n\nНапиши відповідь:",
        parse_mode="HTML"
    )
    await cb.answer()

@router.message(QAS.answer)
async def qa_save_ans(message: Message, state: FSMContext):
    data = await state.get_data()
    qid = data.get("qid")
    await state.clear()
    t = message.text.strip()
    if len(t) < 2:
        await message.answer("❌ Відповідь занадто коротка.")
        return
    qs = load()
    for q in qs:
        if q["id"] == qid:
            q["answers"].append({"text":t,"created":datetime.now().strftime("%d.%m.%Y %H:%M")})
            break
    save(qs)
    await message.answer(
        f"✅ <b>Відповідь на #{qid} додано!</b>", parse_mode="HTML"
    )