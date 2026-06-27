from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from scrapers.news_scraper import get_news, format_news
from services.currency import get_currency, get_currency_detail, TARGET
from services.weather import get_weather

router = Router()


def currency_kb() -> InlineKeyboardMarkup:
    """Кнопки для перегляду деталей кожної валюти."""
    codes = ["USD", "EUR", "GBP", "CHF", "CAD", "PLZ"]
    row1 = [InlineKeyboardButton(text=c, callback_data=f"cur:{c}") for c in codes[:3]]
    row2 = [InlineKeyboardButton(text=c, callback_data=f"cur:{c}") for c in codes[3:]]
    return InlineKeyboardMarkup(inline_keyboard=[
        row1, row2,
        [InlineKeyboardButton(text="🔄 Оновити", callback_data="cur:refresh")],
    ])


@router.message(F.text == "📰 Новини ТНТУ")
async def news_handler(message: Message):
    msg = await message.answer("⏳ Завантажую новини...")
    await msg.edit_text(
        format_news(get_news(7)),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(F.text == "💵 Курс валют")
async def currency_handler(message: Message):
    msg = await message.answer("⏳ Завантажую курс з rulya-bank.com.ua...")
    await msg.edit_text(
        get_currency(),
        parse_mode="HTML",
        reply_markup=currency_kb(),
        disable_web_page_preview=True
    )


@router.callback_query(F.data.startswith("cur:"))
async def currency_detail(callback: CallbackQuery):
    code = callback.data.split(":")[1]

    if code == "refresh":
        # Примусово скидаємо кеш і оновлюємо
        import services.currency as cur_mod
        cur_mod._cache = {"data": [], "ts": 0.0, "update_label": ""}
        await callback.message.edit_text(
            "⏳ Оновлюю курс...",
            parse_mode="HTML"
        )
        await callback.answer("🔄 Оновлюю...")
        await callback.message.edit_text(
            get_currency(),
            parse_mode="HTML",
            reply_markup=currency_kb(),
            disable_web_page_preview=True
        )
        return

    text = get_currency_detail(code)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Всі валюти", callback_data="cur:back")]
    ])
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=back_kb,
        disable_web_page_preview=True
    )
    await callback.answer()


@router.callback_query(F.data == "cur:back")
async def currency_back(callback: CallbackQuery):
    await callback.message.edit_text(
        get_currency(),
        parse_mode="HTML",
        reply_markup=currency_kb(),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.message(F.text == "🌤 Погода")
async def weather_handler(message: Message):
    msg = await message.answer("⏳ Перевіряю погоду в Тернополі...")
    await msg.edit_text(get_weather(), parse_mode="HTML")