# TNTU Helper Bot 🤖

> A Telegram bot for students of Ternopil Ivan Puluj National Technical University

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.7-green.svg)](https://aiogram.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

| Feature | Description |
|---|---|
| 📅 Class Schedule | PDF schedules for all groups and faculties, scraped from tntu.edu.ua |
| 📝 Exam Schedule | Live exam dates, times and rooms for any group |
| 🎓 Grades & ECTS | Average grade calculator, ECTS converter, exam score planner |
| 👨‍🏫 Teachers | Search 200+ teachers across all departments with schedule links |
| 🌤 Weather | Current weather in Ternopil via OpenWeatherMap API |
| 💵 Currency | Live USD/EUR/PLN rates from National Bank of Ukraine (no API key needed) |
| 📰 TNTU News | Latest news scraped from tntu.edu.ua (cached 30 min) |
| 🏛 Buildings | All 11 TNTU buildings with addresses, hours and maps |
| ⏰ Reminders | Personal reminders at any date and time |
| 📋 Deadlines | Deadline tracker with automatic morning alerts at 8:00 AM |
| 📝 Notes | Quick personal notes saved per user |
| ❓ Q&A | Anonymous questions and answers for student community |
| 🎯 Quiz | Subject-based quiz with scoring (CS, Math, Networks, Web, Security) |
| 💬 FAQ | Answers to 20 common student questions (grades, documents, dorms, etc.) |

## Tech Stack

- **Python 3.11+**
- **aiogram 3.7** — async Telegram bot framework
- **APScheduler** — background tasks (reminders, morning deadline alerts)
- **requests + BeautifulSoup4** — web scraping from tntu.edu.ua
- **python-dotenv** — environment variable management
- **JSON files** — lightweight storage for user data (no database required)

## Project Structure

```
tntu_bot/
├── main.py              # Entry point, bot startup + APScheduler
├── config.py            # Settings loaded from .env
├── requirements.txt
├── .env                 # Tokens (not committed to git)
│
├── handlers/            # Telegram command and button handlers
│   ├── start.py         # /start, /help, main menu
│   ├── schedule.py      # Class and exam schedules
│   ├── services.py      # Weather, currency, news
│   ├── grades.py        # Grade calculator + ECTS
│   ├── teachers.py      # Teacher search
│   ├── notes.py         # Personal notes
│   ├── deadlines.py     # Deadline tracker
│   ├── reminders.py     # Personal reminders
│   ├── qa.py            # Anonymous Q&A
│   ├── quiz.py          # Quiz game
│   ├── buildings.py     # Campus buildings
│   └── faq.py           # Student FAQ
│
├── scrapers/            # Web scrapers for tntu.edu.ua
│   ├── schedule_scraper.py
│   ├── news_scraper.py
│   └── teachers_scraper.py
│
├── services/            # External API clients
│   ├── weather.py       # OpenWeatherMap
│   └── currency.py      # National Bank of Ukraine
│
└── data/                # Auto-created JSON storage
    ├── teachers.json    # Teachers database (run scraper to populate)
    ├── quiz.json        # Quiz questions
    ├── users.json       # User preferences
    ├── notes.json       # User notes
    ├── deadlines.json   # User deadlines
    └── reminders.json   # User reminders
```

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/tntu_bot.git
cd tntu_bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

```env
BOT_TOKEN=your_telegram_bot_token_from_@BotFather
WEATHER_API_KEY=your_free_key_from_openweathermap.org
```

### 4. Populate the teachers database

```bash
python -m scrapers.teachers_scraper
```

### 5. Run the bot

```bash
python main.py
```

## Deployment

Deploy for free on [Railway](https://railway.app) or [Render](https://render.com):

1. Push code to GitHub (ensure `.env` is in `.gitignore`)
2. Connect your repository to Railway/Render
3. Set environment variables `BOT_TOKEN` and `WEATHER_API_KEY` in the platform dashboard
4. Deploy — the bot will run 24/7

## Contributing

Feel free to open issues or pull requests. To add more quiz questions, edit `data/quiz.json`.

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

*Created by [YOUR_NAME](https://github.com/YOUR_USERNAME) — 1st year Software Engineering student at TNTU named after Ivan Puluj, Ternopil, Ukraine*