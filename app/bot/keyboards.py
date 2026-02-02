from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Основная клавиатура меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Задать вопрос ИИ")],
            [KeyboardButton(text="⚖️ Трудовой кодекс"), KeyboardButton(text="📊 СОУТ 426-ФЗ")],
            [KeyboardButton(text="🎓 Обучение по ОТ"), KeyboardButton(text="🏢 СУОТ")],
            [KeyboardButton(text="📄 Шаблоны документов"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел или задайте вопрос..."
    )

def get_templates_keyboard():
    """Клавиатура для шаблонов документов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Программа обучения", callback_data="template_program")],
            [InlineKeyboardButton(text="📋 Приказ о создании комиссии", callback_data="template_order")],
            [InlineKeyboardButton(text="📄 Журнал инструктажа", callback_data="template_journal")],
            [InlineKeyboardButton(text="📑 Положение о СУОТ", callback_data="template_regulation")],
        ]
    )

def get_law_keyboard():
    """Клавиатура для разделов законодательства"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ТК РФ: Общие положения", callback_data="law_tk_general")],
            [InlineKeyboardButton(text="ТК РФ: Охрана труда", callback_data="law_tk_safety")],
            [InlineKeyboardButton(text="ТК РФ: Отпуска", callback_data="law_tk_vacation")],
            [InlineKeyboardButton(text="426-ФЗ: СОУТ", callback_data="law_426_sout")],
            [InlineKeyboardButton(text="2464: Обучение по ОТ", callback_data="law_2464_learning")],
        ]
    )
