from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

ECTS = [
    (90,100,"A","Відмінно","✅"),(82,89,"B","Добре","✅"),
    (74,81,"C","Добре","✅"),(64,73,"D","Задовільно","⚠️"),
    (60,63,"E","Задовільно","⚠️"),(35,59,"FX","Незадовільно","❌"),(0,34,"F","Незадовільно","❌"),
]


class GS(StatesGroup):
    avg   = State()
    ects  = State()
    exam1 = State()
    exam2 = State()


def to_ects(score: float):
    for lo,hi,lt,nm,em in ECTS:
        if lo <= score <= hi:
            return lt,nm,em
    return "F","Незадовільно","❌"


@router.message(F.text == "🎓 Оцінки та ECTS")
async def grades_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎓 <b>Оцінки та ECTS</b>\n\n"
        "/avg — Середній бал\n"
        "/ects — Конвертер ECTS\n"
        "/exam — Калькулятор іспиту",
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/avg"))
async def avg_start(message: Message, state: FSMContext):
    await state.set_state(GS.avg)
    await message.answer(
        "📊 <b>Середній бал</b>\n\nВведи оцінки через пробіл або кому:\n"
        "<i>Приклад: 85 90 78 92</i>", parse_mode="HTML"
    )


@router.message(GS.avg)
async def avg_calc(message: Message, state: FSMContext):
    await state.clear()
    try:
        scores = [float(x) for x in message.text.replace(",", " ").split()]
    except ValueError:
        await message.answer("❌ Введи тільки числа, наприклад: <code>85 90 78</code>", parse_mode="HTML")
        return
    if not scores or any(not (0 <= s <= 100) for s in scores):
        await message.answer("❌ Оцінки мають бути від 0 до 100.")
        return
    avg = sum(scores) / len(scores)
    lt, nm, em = to_ects(avg)
    await message.answer(
        f"📊 <b>Результат</b>\n"
        f"{'─'*22}\n"
        f"Введено оцінок: <b>{len(scores)}</b>\n"
        f"Середній бал:  <b>{avg:.2f}</b>\n\n"
        f"{em} ECTS: <b>{lt}</b> — {nm}",
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/ects"))
async def ects_start(message: Message, state: FSMContext):
    await state.set_state(GS.ects)
    await message.answer("🔄 <b>Конвертер ECTS</b>\n\nВведи бал від 0 до 100:", parse_mode="HTML")


@router.message(GS.ects)
async def ects_conv(message: Message, state: FSMContext):
    await state.clear()
    try:
        score = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 0 до 100.")
        return
    if not (0 <= score <= 100):
        await message.answer("❌ Бал має бути від 0 до 100.")
        return
    lt, nm, em = to_ects(score)
    rows = []
    for lo,hi,l,n,e in ECTS:
        mark = "▶" if l == lt else " "
        rows.append(f"{mark} {e} {lo}–{hi} → <b>{l}</b> ({n})")
    await message.answer(
        f"🔄 <b>Конвертер ECTS</b>\n"
        f"Твій бал: <b>{score:.0f}</b>\n"
        f"{'─'*22}\n" + "\n".join(rows) +
        f"\n{'─'*22}\n{em} Результат: <b>{lt}</b> — {nm}",
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/exam"))
async def exam_start(message: Message, state: FSMContext):
    await state.set_state(GS.exam1)
    await message.answer(
        "📝 <b>Калькулятор іспиту</b>\n\n"
        "Крок 1/2 — Введи <b>поточний бал</b> за семестр (0–100):",
        parse_mode="HTML"
    )


@router.message(GS.exam1)
async def exam_curr(message: Message, state: FSMContext):
    try:
        curr = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 0 до 100.")
        return
    if not (0 <= curr <= 100):
        await message.answer("❌ Бал має бути від 0 до 100.")
        return
    await state.update_data(current=curr)
    await state.set_state(GS.exam2)
    await message.answer(
        f"Поточний бал: <b>{curr:.0f}</b>\n\n"
        f"Крок 2/2 — Введи <b>бажану підсумкову оцінку</b> (60–100):",
        parse_mode="HTML"
    )


@router.message(GS.exam2)
async def exam_result(message: Message, state: FSMContext):
    data = await state.get_data()
    curr = data["current"]
    await state.clear()
    try:
        want = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 0 до 100.")
        return
    needed = (want - curr * 0.6) / 0.4
    lt, nm, em = to_ects(want)

    lines = [
        f"📝 <b>Результат</b>",
        f"{'─'*22}",
        f"Поточний бал:  <b>{curr:.0f}</b>",
        f"Бажана оцінка: <b>{want:.0f}</b> ({em} {lt} — {nm})",
        f"{'─'*22}",
    ]
    if needed > 100:
        max_f = curr * 0.6 + 100 * 0.4
        ml, mn, me = to_ects(max_f)
        lines.append(f"😔 Недосяжно навіть при 100 на іспиті.")
        lines.append(f"📌 Максимум: <b>{max_f:.1f}</b> ({me} {ml} — {mn})")
    elif needed < 0:
        lines.append("🎉 Вже досяг! Можеш не хвилюватись.")
    else:
        lines.append(f"🎯 Потрібно на іспиті: <b>{needed:.1f}</b> балів")
        lines.append(f"\n<i>Що потрібно для різних оцінок:</i>")
        for lo,hi,l,n,e in ECTS:
            n_ = (lo - curr * 0.6) / 0.4
            if 0 <= n_ <= 100:
                lines.append(f"  {e} {l}: <b>{n_:.0f}</b> балів на іспиті")
            elif n_ < 0:
                lines.append(f"  {e} {l}: вже маєш ✅")

    lines.append(f"\n<i>Формула: поточний × 0.6 + іспит × 0.4</i>")
    await message.answer("\n".join(lines), parse_mode="HTML")