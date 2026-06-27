from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

MENU = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="📅 Розклад занять"),   KeyboardButton(text="📝 Розклад екзаменів")],
    [KeyboardButton(text="🎓 Оцінки та ECTS"),   KeyboardButton(text="👨‍🏫 Викладачі")],
    [KeyboardButton(text="🌤 Погода"),            KeyboardButton(text="💵 Курс валют")],
    [KeyboardButton(text="📰 Новини ТНТУ"),       KeyboardButton(text="🏛 Корпуси ТНТУ")],
    [KeyboardButton(text="⏰ Нагадування"),       KeyboardButton(text="📋 Дедлайни")],
    [KeyboardButton(text="📝 Нотатки"),           KeyboardButton(text="❓ Q&A")],
    [KeyboardButton(text="🎯 Вікторина"),         KeyboardButton(text="💬 FAQ")],
])


@router.message(CommandStart())
async def cmd_start(message: Message):
    name = message.from_user.first_name
    await message.answer(
        f"👋 Привіт, <b>{name}</b>!\n\n"
        "Я — бот-помічник для студентів\n"
        "<b>ТНТУ імені Івана Пулюя</b> 🎓\n\n"
        "Обери розділ у меню нижче 👇",
        parse_mode="HTML",
        reply_markup=MENU
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>📖 Всі функції бота</b>\n\n"
        "📅 <b>Розклад занять</b> — PDF для будь-якої групи\n"
        "📝 <b>Розклад екзаменів</b> — дати іспитів з сайту ТНТУ\n"
        "🎓 <b>Оцінки та ECTS</b> — калькулятори балів\n"
        "👨‍🏫 <b>Викладачі</b> — пошук по всьому університету\n"
        "🌤 <b>Погода</b> — поточна погода в Тернополі\n"
        "💵 <b>Курс валют</b> — офіційний курс НБУ\n"
        "📰 <b>Новини</b> — останні новини ТНТУ\n"
        "🏛 <b>Корпуси</b> — 11 корпусів та 3 гуртожитки\n"
        "⏰ <b>Нагадування</b> — особисті нагадування\n"
        "📋 <b>Дедлайни</b> — трекер здачі робіт\n"
        "📝 <b>Нотатки</b> — швидкі записи\n"
        "❓ <b>Q&A</b> — анонімні питання\n"
        "🎯 <b>Вікторина</b> — тест знань\n"
        "💬 <b>FAQ</b> — відповіді на типові питання\n\n"
        "Підтримка: @tntu_helper_bot",
        parse_mode="HTML"
    )