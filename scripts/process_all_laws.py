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

def check_files(data_dir: Path):
    """Проверяет и выводит информацию о файлах."""
    text_files = list(data_dir.glob("*.txt"))
    
    if not text_files:
        logger.error("❌ Нет текстовых файлов (.txt)")
        return []
    
    logger.info(f"📚 Найдено {len(text_files)} документов:")
    for i, file_path in enumerate(text_files, 1):
        try:
            size_kb = file_path.stat().st_size / 1024
            # Читаем первые 100 символов для проверки
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                preview = f.read(100).replace('\n', ' ')
            logger.info(f"  {i}. {file_path.name} ({size_kb:.1f} КБ)")
            logger.info(f"     Начало: {preview}...")
        except Exception as e:
            logger.error(f"  {i}. {file_path.name} - ОШИБКА ЧТЕНИЯ: {e}")
    
    return text_files

def main():
    """Основная функция обработки документов."""
    logger.info("🚀 Запуск обработки документов по охране труда")
    logger.info("=" * 60)
    
    # Путь к данным
    data_dir = Path(__file__).parent.parent / "data" / "texts"
    
    if not data_dir.exists():
        logger.error(f"❌ Папка не найдена: {data_dir}")
        logger.info("Создайте папку data/texts/ и добавьте файлы .txt")
        return
    
    # Проверяем файлы
    text_files = check_files(data_dir)
    if not text_files:
        return
    
    # Создаем базу знаний
    try:
        from app.ai.core import KnowledgeBase
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать KnowledgeBase: {e}")
        logger.info("Проверьте файл app/ai/core.py")
        return
    
    logger.info("\n🧠 Создаю базу знаний...")
    
    try:
        kb = KnowledgeBase()
        logger.info(f"✅ База знаний создана")
        logger.info(f"📊 Изначально фрагментов: {kb.get_document_count()}")
        
        # ЗАГРУЖАЕМ документы - ВАЖНЫЙ ЭТАП!
        logger.info(f"\n📥 Загружаю {len(text_files)} файлов в базу знаний...")
        kb.load_documents(text_files)
        
        # Проверяем результат загрузки
        doc_count = kb.get_document_count()
        logger.info(f"📊 Фрагментов загружено: {doc_count}")
        
        if doc_count == 0:
            logger.error("❌ База знаний осталась пустой!")
            logger.info("Возможные причины:")
            logger.info("1. Файлы пустые или содержат только RTF-код")
            logger.info("2. Ошибка в методе load_documents()")
            logger.info("3. Проблемы с кодировкой файлов")
            return
        
        # Тестируем поиск
        logger.info("\n🔍 Тестирую поиск...")
        
        test_queries = [
            ("отпуск", "ТК РФ"),
            ("специальная оценка", "426-ФЗ"),
            ("обучение", "2464"),
            ("охрана труда", "любой документ")
        ]
        
        successful_searches = 0
        
        for query, expected in test_queries:
            logger.info(f"\n  Поиск: '{query}' (ожидается в {expected})")
            results = kb.search(query, k=1)
            
            if results:
                successful_searches += 1
                doc, score = results[0]
                source = doc.metadata.get('source', 'Документ')
                logger.info(f"    ✅ Найдено в: {source} (релевантность: {score:.3f})")
                
                # Показываем начало текста
                preview = doc.page_content[:100].replace('\n', ' ')
                logger.info(f"    📄 {preview}...")
            else:
                logger.info(f"    ❌ Не найдено")
        
        # Статистика
        logger.info("\n" + "=" * 60)
        logger.info("📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   • Файлов обработано: {len(text_files)}")
        logger.info(f"   • Фрагментов в базе: {doc_count}")
        logger.info(f"   • Успешных поисков: {successful_searches}/{len(test_queries)}")
        
        if successful_searches > 0:
            logger.info("\n🎉 Обработка завершена успешно!")
            logger.info("Теперь можно запускать бота:")
            logger.info("cd app && python main.py")
        else:
            logger.warning("\n⚠️  Обработка завершена, но поиск не работает")
            logger.info("Проверьте содержимое файлов и метод search()")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
