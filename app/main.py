import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Добавляем путь для импорта модулей
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Пытаемся импортировать базу знаний
try:
    # Сначала пробуем легкую версию
    from app.ai.core_light import KnowledgeBase
    kb = KnowledgeBase()
    AI_ENABLED = True
    logging.info("✅ Облегченная база знаний загружена")
    
    # Проверяем, есть ли документы
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "data" / "texts"
    if data_dir.exists():
        files = list(data_dir.glob("*.txt"))
        if files:
            kb.load_documents(files[:2])  # Загружаем первые 2 файла
            logging.info(f"📚 Загружено документов: {kb.get_document_count()}")
        else:
            logging.warning("⚠️ Нет текстовых файлов в data/texts/")
    else:
        logging.warning("⚠️ Папка data/texts/ не найдена")
        
except ImportError as e:
    logging.warning(f"❌ Не удалось загрузить базу знаний: {e}")
    logging.warning("Бот будет работать в простом режиме")
    kb = None
    AI_ENABLED = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ Не найден BOT_TOKEN в .env файле!")
    logger.info("Создайте файл .env в корне проекта с содержимым:")
    logger.info("BOT_TOKEN=ваш_токен_от_BotFather")
    exit(1)

# Создаем объекты бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния для FSM (Finite State Machine)
class SearchStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_law_type = State()

# Улучшенная клавиатура
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Задать вопрос ИИ")],
            [
                KeyboardButton(text="⚖️ ТК РФ"),
                KeyboardButton(text="📊 СОУТ"),
                KeyboardButton(text="🎓 Обучение")
            ],
            [
                KeyboardButton(text="🏢 СУОТ"),
                KeyboardButton(text="📄 Инструкции"),
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Обработчик /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 **Бот-ассистент по охране труда**\n\n"
        "Я помогу найти информацию в нормативных документах:\n"
        "• Трудовой кодекс РФ\n"
        "• 426-ФЗ 'О специальной оценке условий труда'\n"
        "• Постановление №2464 'Об обучении'\n"
        "• Приказы Минтруда №776н и №772н\n\n"
        "Используйте меню или просто задайте вопрос!"
    )
    
    status_text = "✅ ИИ-поиск активен" if AI_ENABLED else "⚠️ ИИ-поиск временно недоступен"
    
    await message.answer(
        f"{welcome_text}\n\n{status_text}",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# Обработчик /help
@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    help_text = (
        "🆘 **Помощь по использованию бота:**\n\n"
        "**Основные функции:**\n"
        "• `🔍 Задать вопрос ИИ` — поиск по всем документам\n"
        "• `⚖️ ТК РФ` — вопросы по Трудовому кодексу\n"
        "• `📊 СОУТ` — специальная оценка условий труда\n"
        "• `🎓 Обучение` — обучение по охране труда\n"
        "• `🏢 СУОТ` — система управления охраной труда\n"
        "• `📄 Инструкции` — правила и инструкции по ОТ\n\n"
        "**Примеры вопросов:**\n"
        "• _Сколько дней ежегодного отпуска?_\n"
        "• _Как проводится специальная оценка?_\n"
        "• _Кто должен проходить обучение по ОТ?_\n"
        "• _Что должно быть в инструкции по охране труда?_\n\n"
        "Просто напишите вопрос или выберите раздел из меню!"
    )
    await message.answer(help_text, parse_mode="Markdown")

# Обработчик кнопки "Задать вопрос ИИ"
@dp.message(F.text == "🔍 Задать вопрос ИИ")
async def ask_ai_question(message: Message, state: FSMContext):
    if not AI_ENABLED:
        await message.answer(
            "⚠️ ИИ-поиск временно недоступен.\n"
            "Проверьте, установлены ли все зависимости:\n"
            "`pip install -r requirements.txt`",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.set_state(SearchStates.waiting_for_question)
    await message.answer(
        "💡 **Режим интеллектуального поиска**\n\n"
        "Задайте ваш вопрос по охране труда, и я найду "
        "ответы во всех нормативных документах.\n\n"
        "Например:\n"
        "• _Какие обязанности у работодателя по охране труда?_\n"
        "• _Как проводится инструктаж на рабочем месте?_\n"
        "• _Что такое вредные условия труда?_\n\n"
        "Или нажмите `❌ Отмена` для возврата в меню.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

# Обработчик отмены
@dp.message(F.text == "❌ Отмена")
async def cancel_search(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👌 Поиск отменен.",
        reply_markup=get_main_keyboard()
    )

# Обработчик текстовых вопросов (когда ждем вопрос)
@dp.message(SearchStates.waiting_for_question)
async def process_ai_question(message: Message, state: FSMContext):
    user_question = message.text.strip()
    
    if not user_question or len(user_question) < 3:
        await message.answer("Пожалуйста, задайте более конкретный вопрос (минимум 3 символа).")
        return
    
    # Информируем о начале поиска
    search_msg = await message.answer("🔍 Ищу информацию в документах...")
    
    try:
        # Анализируем запрос
        query_analysis = kb.analyze_query(user_question)
        
        # Ищем ответы
        search_results = kb.search(user_question, k=3)
        
        if not search_results:
            await search_msg.edit_text(
                f"❌ По запросу '{user_question}' ничего не найдено.\n\n"
                "Попробуйте:\n"
                "• Переформулировать вопрос\n"
                "• Использовать другие ключевые слова\n"
                "• Выбрать конкретный раздел из меню"
            )
            await state.clear()
            await message.answer("Выберите действие:", reply_markup=get_main_keyboard())
            return
        
        # Формируем ответ
        response_parts = []
        response_parts.append(f"📄 **Результаты поиска по запросу:**\n`{user_question}`\n")
        
        # Показываем анализ запроса
        if query_analysis['suggested_laws']:
            response_parts.append("📊 **Наиболее релевантные разделы:**")
            for law_key, score in query_analysis['suggested_laws'][:2]:
                law_info = kb.get_law_info(law_key)
                response_parts.append(f"• {law_info['name']}")
        
        response_parts.append("\n---\n")
        
        # Показываем найденные фрагменты
        for i, (doc, relevance) in enumerate(search_results, 1):
            source = doc.metadata.get('source', 'Документ')
            content = doc.page_content
            
            # Обрезаем длинный текст
            if len(content) > 400:
                content = content[:400] + "..."
            
            response_parts.append(
                f"**{i}. {source}**\n"
                f"_(релевантность: {relevance:.2f})_\n"
                f"{content}\n"
            )
        
        response_parts.append(
            "\n---\n"
            "💡 _Информация предоставлена на основе анализа нормативных документов. "
            "Для принятия решений обратитесь к оригинальным источникам._"
        )
        
        full_response = "\n".join(response_parts)
        
        # Разбиваем длинное сообщение на части (Telegram ограничение 4096 символов)
        if len(full_response) > 4000:
            parts = []
            current_part = ""
            for line in full_response.split('\n'):
                if len(current_part) + len(line) + 1 < 4000:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'
            if current_part:
                parts.append(current_part)
            
            # Отправляем первую часть
            await search_msg.edit_text(parts[0], parse_mode="Markdown")
            
            # Отправляем остальные части
            for part in parts[1:]:
                await message.answer(part, parse_mode="Markdown")
        else:
            await search_msg.edit_text(full_response, parse_mode="Markdown")
        
        # Очищаем состояние и возвращаем в меню
        await state.clear()
        await message.answer(
            "🔍 Хотите задать еще один вопрос?",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}", exc_info=True)
        await search_msg.edit_text(
            f"⚠️ Произошла ошибка при поиске:\n\n`{str(e)}`\n\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )
        await state.clear()
        await message.answer("Выберите действие:", reply_markup=get_main_keyboard())

# Обработчики для конкретных разделов
@dp.message(F.text.in_(["⚖️ ТК РФ", "📊 СОУТ", "🎓 Обучение", "🏢 СУОТ", "📄 Инструкции"]))
async def handle_specific_law(message: Message):
    law_map = {
        "⚖️ ТК РФ": ("tk_rf", "Трудовой кодекс РФ"),
        "📊 СОУТ": ("426_fz", "Федеральный закон №426-ФЗ 'О СОУТ'"),
        "🎓 Обучение": ("2464_pp", "Постановление №2464 'Об обучении по ОТ'"),
        "🏢 СУОТ": ("776n_prikaz", "Приказ №776н 'О системе управления охраной труда'"),
        "📄 Инструкции": ("772n_prikaz", "Приказ №772н 'О правилах и инструкциях'")
    }
    
    law_key, law_name = law_map[message.text]
    
    law_info = kb.get_law_info(law_key) if AI_ENABLED else {"name": law_name, "description": "Информация временно недоступна"}
    
    response_text = (
        f"📚 **{law_info['name']}**\n\n"
        f"{law_info.get('description', 'Раздел в разработке')}\n\n"
    )
    
    if 'topics' in law_info:
        response_text += "**Основные темы:**\n"
        for topic in law_info['topics']:
            response_text += f"• {topic}\n"
    
    response_text += (
        f"\n💡 **Примеры вопросов для этого раздела:**\n"
        f"• Задайте вопрос в свободной форме\n"
        f"• Или нажмите `🔍 Задать вопрос ИИ` для поиска по всем документам"
    )
    
    await message.answer(response_text, parse_mode="Markdown")

# Обработчик всех остальных текстовых сообщений
@dp.message()
async def handle_general_message(message: Message):
    user_text = message.text
    
    # Если это не команда и не кнопка, предлагаем использовать ИИ-поиск
    await message.answer(
        f"🔍 Вы написали: `{user_text}`\n\n"
        "Чтобы найти ответ на этот вопрос в нормативных документах, "
        "нажмите кнопку **`🔍 Задать вопрос ИИ`** или выберите конкретный раздел из меню.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# Запуск бота
async def main():
    logger.info("🚀 Запуск бота по охране труда...")
    
    if AI_ENABLED:
        logger.info("✅ ИИ-поиск активен")
        # Проверяем наличие документов
        doc_count = kb.get_document_count()
        logger.info(f"📚 Документов в базе: {doc_count}")
        
        if doc_count == 0:
            logger.warning("⚠️ База знаний пуста. Запустите: python scripts/process_all_laws.py")
    else:
        logger.warning("⚠️ ИИ-поиск отключен. Бот работает в простом режиме.")
    
    logger.info("✅ Бот запущен и готов к работе!")
    logger.info("👤 Перейдите в Telegram и найдите вашего бота")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота...")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
