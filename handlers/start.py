from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📅 Розклад занять"), KeyboardButton(text="📝 Розклад екзаменів")],
        [KeyboardButton(text="🎓 Оцінки та ECTS"),  KeyboardButton(text="👨‍🏫 Викладачі")],
        [KeyboardButton(text="🌤 Погода"),           KeyboardButton(text="💵 Курс валют")],
        [KeyboardButton(text="📰 Новини ТНТУ"),      KeyboardButton(text="🏛 Корпуси ТНТУ")],
        [KeyboardButton(text="⏰ Нагадування"),      KeyboardButton(text="📋 Дедлайни")],
        [KeyboardButton(text="📝 Нотатки"),          KeyboardButton(text="❓ Q&A")],
        [KeyboardButton(text="🎯 Вікторина"),        KeyboardButton(text="💬 FAQ")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    name = message.from_user.first_name
    await message.answer(
        f"👋 Привіт, {name}!\n\n"
        "Я — офіційний бот-помічник для студентів\n"
        "ТНТУ імені Івана Пулюя 🎓\n\n"
        "Обери що тебе цікавить 👇",
        reply_markup=main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 Список всіх функцій:\n\n"
        "📅 Розклад занять — PDF розклад для будь-якої групи\n"
        "📝 Розклад екзаменів — дати іспитів з сайту ТНТУ\n"
        "🎓 Оцінки та ECTS — калькулятори балів\n"
        "👨‍🏫 Викладачі — пошук по всьому університету\n"
        "🌤 Погода — поточна погода в Тернополі\n"
        "💵 Курс валют — офіційний курс НБУ\n"
        "📰 Новини — останні новини ТНТУ\n"
        "🏛 Корпуси — адреси і карти корпусів\n"
        "⏰ Нагадування — особисті нагадування\n"
        "📋 Дедлайни — трекер здачі робіт\n"
        "📝 Нотатки — швидкі нотатки\n"
        "❓ Q&A — анонімні питання і відповіді\n"
        "🎯 Вікторина — тест знань по предметах\n"
        "💬 FAQ — відповіді на типові питання студентів"
    )