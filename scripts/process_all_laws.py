#!/usr/bin/env python3
"""
Скрипт для обработки документов по охране труда.
Создает базу знаний из всех законов.
"""

import sys
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция обработки документов."""
    logger.info("🚀 Запуск обработки документов по охране труда")
    logger.info("=" * 60)
    
    # Путь к данным
    data_dir = Path(__file__).parent.parent / "data" / "texts"
    
    if not data_dir.exists():
        logger.error(f"❌ Папка не найдена: {data_dir}")
        return
    
    # Ищем текстовые файлы
    text_files = list(data_dir.glob("*.txt"))
    
    if not text_files:
        logger.error("❌ Нет текстовых файлов (.txt)")
        return
    
    logger.info(f"📚 Найдено {len(text_files)} документов:")
    for i, file_path in enumerate(text_files, 1):
        size_kb = file_path.stat().st_size / 1024
        logger.info(f"  {i}. {file_path.name} ({size_kb:.1f} КБ)")
    
    # Создаем базу знаний
    try:
        from app.ai.core import KnowledgeBase
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать KnowledgeBase: {e}")
        return
    
    logger.info("\n🧠 Создаю базу знаний...")
    kb = KnowledgeBase()
    
    # Загружаем документы
    kb.load_documents(text_files)
    
    # Тестируем поиск
    logger.info("\n🔍 Тестирую поиск...")
    
    test_queries = [
        ("отпуск", "ТК РФ"),
        ("специальная оценка", "426-ФЗ"),
        ("обучение охрана труда", "2464")
    ]
    
    for query, expected in test_queries:
        logger.info(f"\n  Поиск: '{query}' (ожидается в {expected})")
        results = kb.search(query, k=1)
        
        if results:
            doc, score = results[0]
            source = doc.metadata.get('source', 'Документ')
            logger.info(f"    ✅ Найдено в: {source} (релевантность: {score:.3f})")
            
            # Показываем начало текста
            preview = doc.page_content[:100].replace('\n', ' ')
            logger.info(f"    📄 {preview}...")
        else:
            logger.info(f"    ❌ Не найдено")
    
    # Статистика
    logger.info("\n📊 СТАТИСТИКА:")
    logger.info(f"   • Файлов обработано: {len(text_files)}")
    logger.info(f"   • Фрагментов в базе: {kb.get_document_count()}")
    
    logger.info("\n🎉 Обработка завершена!")
    logger.info("Теперь запустите бота: cd app && python main.py")

if __name__ == "__main__":
    main()
