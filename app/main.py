import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ Не найден BOT_TOKEN в .env файле!")
    exit(1)

# Создаем объекты бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Клавиатура
def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Задать вопрос")],
            [KeyboardButton(text="⚖️ Трудовой кодекс")],
            [KeyboardButton(text="📋 Шаблоны документов")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

# Обработчик /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот-ассистент по охране труда.\n\n"
        "Я помогу вам найти информацию в нормативных документах.\n"
        "Используйте меню или просто задайте вопрос!",
        reply_markup=get_keyboard()
    )

# Обработчик /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🆘 **Помощь по боту:**\n\n"
        "• Напишите любой вопрос по охране труда\n"
        "• Или выберите раздел в меню\n\n"
        "Примеры вопросов:\n"
        "• _Сколько дней отпуска?_ \n"
        "• _Обязанности работодателя по охране труда_\n"
        "• _Что такое СОУТ?_"
    )

# Обработчик текстовых сообщений
@dp.message()
async def handle_message(message: Message):
    user_text = message.text
    
    if user_text == "❓ Задать вопрос":
        await message.answer("Задайте ваш вопрос по охране труда...")
    elif user_text == "⚖️ Трудовой кодекс":
        await message.answer("Раздел 'Трудовой кодекс' в разработке...")
    elif user_text == "📋 Шаблоны документов":
        await message.answer("Раздел 'Шаблоны документов' в разработке...")
    elif user_text == "ℹ️ Помощь":
        await cmd_help(message)
    else:
        # Пока простой ответ
        await message.answer(
            f"🔍 Ваш вопрос: '{user_text}'\n\n"
            f"ИИ-модуль поиска по документам в разработке.\n"
            f"Скоро я смогу искать ответы в Трудовом кодексе!"
        )

# Запуск бота
async def main():
    logger.info("🚀 Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
