from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from scrapers.news_scraper import get_news, format_news
from services.currency import get_currency, get_currency_detail
from services.weather import get_weather

router = Router()

CURRENCY_CODES = ["USD", "EUR", "GBP", "CHF", "CAD", "PLZ"]


def currency_main_kb() -> InlineKeyboardMarkup:
    r1 = [InlineKeyboardButton(text=c, callback_data=f"cur_d:{c}") for c in CURRENCY_CODES[:3]]
    r2 = [InlineKeyboardButton(text=c, callback_data=f"cur_d:{c}") for c in CURRENCY_CODES[3:]]
    return InlineKeyboardMarkup(inline_keyboard=[
        r1, r2,
        [InlineKeyboardButton(text="🔄 Оновити", callback_data="cur_refresh")],
    ])


def currency_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Всі валюти", callback_data="cur_back")]
    ])


@router.message(F.text == "📰 Новини ТНТУ")
async def news_handler(message: Message):
    msg = await message.answer("⏳ Завантажую новини...")
    await msg.edit_text(format_news(get_news(7)),
                        parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "💵 Курс валют")
async def currency_handler(message: Message):
    msg = await message.answer("⏳ Завантажую курс з rulya-bank.com.ua...")
    await msg.edit_text(get_currency(), parse_mode="HTML",
                        reply_markup=currency_main_kb(),
                        disable_web_page_preview=True)


@router.callback_query(F.data == "cur_refresh")
async def currency_refresh(callback: CallbackQuery):
    import services.currency as m
    m._cache = {"data": [], "ts": 0.0, "update_label": ""}
    await callback.message.edit_text("⏳ Оновлюю...", parse_mode="HTML")
    await callback.answer("🔄 Оновлюю...")
    await callback.message.edit_text(get_currency(), parse_mode="HTML",
                                     reply_markup=currency_main_kb(),
                                     disable_web_page_preview=True)


@router.callback_query(F.data == "cur_back")
async def currency_back(callback: CallbackQuery):
    await callback.message.edit_text(get_currency(), parse_mode="HTML",
                                     reply_markup=currency_main_kb(),
                                     disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("cur_d:"))
async def currency_detail(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    await callback.message.edit_text(get_currency_detail(code), parse_mode="HTML",
                                     reply_markup=currency_back_kb(),
                                     disable_web_page_preview=True)
    await callback.answer()


@router.message(F.text == "🌤 Погода")
async def weather_handler(message: Message):
    msg = await message.answer("⏳ Перевіряю погоду в Тернополі...")
    await msg.edit_text(get_weather(), parse_mode="HTML")