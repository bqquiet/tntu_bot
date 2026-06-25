from aiogram import Router, F
from aiogram.types import Message

from scrapers.news_scraper import get_news, format_news
from services.currency import get_currency
from services.weather import get_weather

router = Router()


@router.message(F.text == "📰 Новини ТНТУ")
async def news_handler(message: Message):
    msg = await message.answer("⏳ Завантажую новини...")
    news = get_news(limit=7)
    text = format_news(news)
    # Без parse_mode — новини містять крапки, дефіси та інші спецсимволи
    await msg.edit_text(text, disable_web_page_preview=True)


@router.message(F.text == "💵 Курс валют")
async def currency_handler(message: Message):
    msg = await message.answer("⏳ Отримую курс НБУ...")
    text = get_currency()
    await msg.edit_text(text)


@router.message(F.text == "🌤 Погода")
async def weather_handler(message: Message):
    msg = await message.answer("⏳ Перевіряю погоду в Тернополі...")
    text = get_weather()
    await msg.edit_text(text)