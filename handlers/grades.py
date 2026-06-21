from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# ─── Таблиця ECTS ────────────────────────────────────────────────────────────

ECTS_TABLE = [
    (90, 100, "A", "Відмінно",     "✅"),
    (82,  89, "B", "Добре",        "✅"),
    (74,  81, "C", "Добре",        "✅"),
    (64,  73, "D", "Задовільно",   "⚠️"),
    (60,  63, "E", "Задовільно",   "⚠️"),
    (35,  59, "FX","Незадовільно", "❌"),
    ( 0,  34, "F", "Незадовільно", "❌"),
]

def score_to_ects(score: float) -> tuple[str, str, str]:
    """Повертає (літера, назва, емодзі) для заданого балу."""
    for low, high, letter, name, emoji in ECTS_TABLE:
        if low <= score <= high:
            return letter, name, emoji
    return "F", "Незадовільно", "❌"

# ─── FSM-стани ───────────────────────────────────────────────────────────────

class GradeStates(StatesGroup):
    waiting_for_grades    = State()   # середній бал
    waiting_for_ects      = State()   # конвертер ECTS
    waiting_for_exam_calc = State()   # калькулятор іспиту — крок 1 (поточний бал)
    waiting_for_exam_want = State()   # калькулятор іспиту — крок 2 (бажана оцінка)

# ─── Головне меню оцінок ─────────────────────────────────────────────────────

@router.message(F.text == "🎓 Оцінки та ECTS")
async def grades_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎓 *Оцінки та ECTS*\n\n"
        "Що хочеш порахувати?\n\n"
        "📊 /avg — Середній бал\n"
        "🔄 /ects — Конвертер ECTS\n"
        "📝 /exam — Скільки треба на іспиті",
        parse_mode="Markdown"
    )

# ─── 1. Середній бал ─────────────────────────────────────────────────────────

@router.message(F.text.startswith("/avg"))
async def avg_start(message: Message, state: FSMContext):
    await state.set_state(GradeStates.waiting_for_grades)
    await message.answer(
        "📊 *Калькулятор середнього балу*\n\n"
        "Введи оцінки через пробіл або кому:\n"
        "_Приклад: 85 90 78 92 67_",
        parse_mode="Markdown"
    )

@router.message(GradeStates.waiting_for_grades)
async def avg_calculate(message: Message, state: FSMContext):
    await state.clear()
    raw = message.text.replace(",", " ").split()

    try:
        scores = [float(s) for s in raw]
    except ValueError:
        await message.answer("❌ Введи лише числа, наприклад: *85 90 78*", parse_mode="Markdown")
        return

    if not scores:
        await message.answer("❌ Не знайдено жодної оцінки.")
        return

    invalid = [s for s in scores if not (0 <= s <= 100)]
    if invalid:
        await message.answer(f"❌ Оцінки мають бути від 0 до 100. Перевір: {invalid}")
        return

    avg = sum(scores) / len(scores)
    letter, name, emoji = score_to_ects(avg)

    lines = [
        f"📊 *Результат*\n",
        f"Оцінок введено: {len(scores)}",
        f"Середній бал: *{avg:.2f}*",
        f"\n{emoji} ECTS: *{letter}* — {name}",
    ]

    # Додаємо міні-таблицю всіх введених оцінок
    if len(scores) > 1:
        score_strs = [f"{int(s) if s == int(s) else s}" for s in scores]
        lines.append(f"\n_Введені оцінки: {', '.join(score_strs)}_")

    await message.answer("\n".join(lines), parse_mode="Markdown")

# ─── 2. Конвертер ECTS ───────────────────────────────────────────────────────

@router.message(F.text.startswith("/ects"))
async def ects_start(message: Message, state: FSMContext):
    await state.set_state(GradeStates.waiting_for_ects)
    await message.answer(
        "🔄 *Конвертер ECTS*\n\n"
        "Введи бал від 0 до 100:",
        parse_mode="Markdown"
    )

@router.message(GradeStates.waiting_for_ects)
async def ects_convert(message: Message, state: FSMContext):
    await state.clear()
    try:
        score = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 0 до 100.")
        return

    if not (0 <= score <= 100):
        await message.answer("❌ Бал має бути від 0 до 100.")
        return

    letter, name, emoji = score_to_ects(score)

    # Повна таблиця для наочності
    table_lines = ["🔄 *Конвертер ECTS*\n"]
    table_lines.append(f"Твій бал: *{score:.0f}*\n")

    for low, high, ltr, nm, emj in ECTS_TABLE:
        marker = "▶️ " if ltr == letter else "    "
        table_lines.append(f"{marker}{emj} {low}–{high} → *{ltr}* ({nm})")

    table_lines.append(f"\n{emoji} Результат: *{letter}* — {name}")
    await message.answer("\n".join(table_lines), parse_mode="Markdown")

# ─── 3. Скільки треба на іспиті ──────────────────────────────────────────────

@router.message(F.text.startswith("/exam"))
async def exam_calc_start(message: Message, state: FSMContext):
    await state.set_state(GradeStates.waiting_for_exam_calc)
    await message.answer(
        "📝 *Калькулятор іспиту*\n\n"
        "Введи свій *поточний бал* за семестр (0–100):\n"
        "_Це бал який ти вже маєш до іспиту_",
        parse_mode="Markdown"
    )

@router.message(GradeStates.waiting_for_exam_calc)
async def exam_calc_current(message: Message, state: FSMContext):
    try:
        current = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 0 до 100.")
        return

    if not (0 <= current <= 100):
        await message.answer("❌ Бал має бути від 0 до 100.")
        return

    await state.update_data(current=current)
    await state.set_state(GradeStates.waiting_for_exam_want)
    await message.answer(
        f"Поточний бал: *{current:.0f}*\n\n"
        "Тепер введи *бажану підсумкову оцінку* (60–100):\n"
        "_Наприклад: 75 (щоб вийти на ECTS C)_",
        parse_mode="Markdown"
    )

@router.message(GradeStates.waiting_for_exam_want)
async def exam_calc_result(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    current = data.get("current", 0)

    try:
        target = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число від 60 до 100.")
        return

    if not (0 <= target <= 100):
        await message.answer("❌ Бал має бути від 0 до 100.")
        return

    # Формула ТНТУ: підсумковий = поточний * 0.6 + іспит * 0.4
    # Звідси: іспит = (підсумковий - поточний * 0.6) / 0.4
    SEMESTER_WEIGHT = 0.6
    EXAM_WEIGHT = 0.4
    needed = (target - current * SEMESTER_WEIGHT) / EXAM_WEIGHT

    letter, name, emoji = score_to_ects(target)

    lines = [f"📝 *Результат калькулятора іспиту*\n"]
    lines.append(f"Поточний бал:    *{current:.0f}*")
    lines.append(f"Бажана оцінка:   *{target:.0f}* ({emoji} {letter} — {name})")
    lines.append("")

    if needed > 100:
        lines.append("😔 На жаль, навіть при максимальному балі на іспиті (100) ця оцінка недосяжна.")
        # Показуємо що максимально можливо
        max_final = current * SEMESTER_WEIGHT + 100 * EXAM_WEIGHT
        max_letter, max_name, max_emoji = score_to_ects(max_final)
        lines.append(f"\n📌 Максимум що можеш отримати: *{max_final:.1f}* ({max_emoji} {max_letter} — {max_name})")
    elif needed < 0:
        lines.append("🎉 Ти вже набрав достатньо! На іспит можеш йти спокійно.")
        lines.append(f"📌 Навіть з 0 на іспиті матимеш ≥ {target:.0f} балів.")
    else:
        lines.append(f"🎯 На іспиті потрібно набрати: *{needed:.1f}* балів")

        # Підказки для інших порогів
        lines.append("\n_Що потрібно для інших оцінок:_")
        for low, high, ltr, nm, emj in ECTS_TABLE:
            n = (low - current * SEMESTER_WEIGHT) / EXAM_WEIGHT
            if 0 <= n <= 100:
                lines.append(f"  {emj} {ltr} ({low}+): потрібно *{n:.0f}* на іспиті")
            elif n < 0:
                lines.append(f"  {emj} {ltr} ({low}+): вже маєш ✅")

    lines.append(f"\n_Формула: поточний × 0.6 + іспит × 0.4_")
    await message.answer("\n".join(lines), parse_mode="Markdown")