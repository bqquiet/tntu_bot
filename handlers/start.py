from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📅 Розклад"), KeyboardButton(text="📝 Екзамени")],
        [KeyboardButton(text="🎓 Оцінки та ECTS"), KeyboardButton(text="👨‍🏫 Викладачі")],
        [KeyboardButton(text="🌤 Погода"), KeyboardButton(text="💵 Курс валют")],
        [KeyboardButton(text="📰 Новини ТНТУ"), KeyboardButton(text="⏰ Нагадування")],
        [KeyboardButton(text="📋 Дедлайни"), KeyboardButton(text="📝 Нотатки")],
        [KeyboardButton(text="❓ Q&A"), KeyboardButton(text="🎯 Вікторина")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привіт, *{message.from_user.first_name}*\\!\n\n"
        "Я — бот\\-помічник для студентів ТНТУ імені Івана Пулюя\\.\n"
        "Обери що тебе цікавить 👇",
        reply_markup=main_menu(),
        parse_mode="MarkdownV2"
    )
