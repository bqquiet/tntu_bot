import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import start, schedule, services, grades, teachers

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Підключаємо роутери
    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(services.router)
    dp.include_router(grades.router)
    dp.include_router(teachers.router)

    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())