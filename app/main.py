import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

# Импортируем наши обработчики
from app.bot.handlers import router as main_router

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT
