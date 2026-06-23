import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import (
    start, schedule, services, grades,
    teachers, notes, deadlines, reminders,
    qa, quiz, buildings, faq
)
from handlers.deadlines import send_morning_deadlines
from handlers.reminders import check_and_send_reminders

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(services.router)
    dp.include_router(grades.router)
    dp.include_router(teachers.router)
    dp.include_router(notes.router)
    dp.include_router(deadlines.router)
    dp.include_router(reminders.router)
    dp.include_router(qa.router)
    dp.include_router(quiz.router)
    dp.include_router(buildings.router)
    dp.include_router(faq.router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_morning_deadlines, "cron", hour=8, minute=0, args=[bot])
    scheduler.add_job(check_and_send_reminders, "interval", minutes=1, args=[bot])
    scheduler.start()

    logging.info("✅ Бот запущено. Всі модулі активні.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())