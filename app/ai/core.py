import os
from pathlib import Path
from typing import List, Tuple, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== БАЗОВЫЕ КЛАССЫ ====================

class Document:
    """Упрощенный класс документа для совместимости."""
    def __init__(self, page_content: str, metadata: Optional[dict] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

# ==================== УПРОЩЕННАЯ БАЗА ЗНАНИЙ ====================

class SimpleKnowledgeBase:
    """Упрощенная база знаний для работы без LangChain."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Инициализация базы знаний.
        
        Args:
            persist_directory: Директория для сохранения (не используется в простой версии)
        """
        self.documents = []
        self.persist_directory = persist_directory or "./data/vector_db"
        
        # Создаем директорию, если её нет
        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info("✅ Упрощенная база знаний инициализирована")
    
    def load_documents(self, file_paths: List[Path]):
        """
        Загружает документы из файлов.
        
        Args:
            file_paths: Список путей к текстовым файлам
        """
        if not file_paths:
            logger.warning("❌ Нет файлов для загрузки")
            return
        
        logger.info(f"📚 Загружаю {len(file_paths)} документов...")
        
        loaded_count = 0
        for file_path in file_paths:
            try:
                # Читаем файл
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().strip()
                
                if not text:
                    logger.warning(f"  ⚠️ Файл пуст: {file_path.name}")
                    continue
                
                # Разбиваем текст на части (упрощенно)
                chunks = self._split_text(text)
                
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": file_path.name,
                            "chunk": i,
                            "file_path": str(file_path)
                        }
                    )
                    self.documents.append(doc)
                
                loaded_count += 1
                logger.info(f"  ✅ {file_path.name}: {len(chunks)} фрагментов")
                
            except Exception as e:
                logger.error(f"  ❌ Ошибка загрузки {file_path.name}: {e}")
        
        logger.info(f"📊 Всего загружено: {len(self.documents)} фрагментов из {loaded_count} файлов")
    
    def _split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Разбивает текст на фрагменты."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Пытаемся разбить по границе предложения
            if end < text_length:
                for separator in ['. ', '.\n', '\n\n', '; ', '! ', '? ']:
                    pos = text.rfind(separator, start, end)
                    if pos != -1:
                        end = pos + len(separator)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Простой поиск по ключевым словам.
        
        Args:
            query: Поисковый запрос
            k: Количество возвращаемых результатов
            
        Returns:
            Список кортежей (документ, оценка релевантности)
        """
        if not self.documents:
            logger.warning("❌ База знаний пуста. Сначала загрузите документы.")
            return []
        
        query_lower = query.lower()
        query_words = [word for word in query_lower.split() if len(word) > 2]
        
        if not query_words:
            logger.warning("⚠️ Запрос слишком короткий")
            return []
        
        results = []
        
        for doc in self.documents:
            content_lower = doc.page_content.lower()
            
            # Простой подсчет совпадений
            score = 0
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            if score > 0:
                # Нормализуем оценку
                normalized_score = min(score / len(query_words), 1.0)
                results.append((doc, normalized_score))
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"🔍 По запросу '{query}' найдено {len(results)} фрагментов")
        return results[:k]
    
    def get_document_count(self) -> int:
        """Возвращает количество документов в базе."""
        return len(self.documents)
    
    def get_db_path(self) -> str:
        """Возвращает путь к директории с БД."""
        return self.persist_directory
    
    def create_vectorstore_from_documents(self):
        """Заглушка для совместимости."""
        logger.info("ℹ️ Векторный поиск недоступен в упрощенной версии")
        return True

# ==================== АЛИАС ДЛЯ СОВМЕСТИМОСТИ ====================

# Основной класс для импорта
KnowledgeBase = SimpleKnowledgeBase

# ==================== ТЕСТИРОВАНИЕ ====================

def test_knowledge_base():
    """Тестирование базы знаний."""
    print("🧪 Тестирование упрощенной базы знаний...")
    print("=" * 60)
    
    kb = KnowledgeBase()
    print(f"✅ База знаний создана")
    print(f"📁 Путь: {kb.get_db_path()}")
    
    # Проверяем наличие документов
    data_dir = Path(__file__).parent.parent.parent / "data" / "texts"
    
    if data_dir.exists():
        txt_files = list(data_dir.glob("*.txt"))
        print(f"\n📚 Найдено {len(txt_files)} TXT файлов:")
        
        for file in txt_files:
            size_kb = file.stat().st_size / 1024 if file.exists() else 0
            print(f"  • {file.name} ({size_kb:.1f} КБ)")
        
        if txt_files:
            # Загружаем документы
            kb.load_documents(txt_files[:1])  # Только первый для теста
            
            # Тестовый поиск
            test_queries = ["отпуск", "охрана труда", "рабочее время"]
            
            for query in test_queries:
                print(f"\n🔍 Поиск: '{query}'")
                results = kb.search(query, k=1)
                
                if results:
                    doc, score = results[0]
                    source = doc.metadata.get('source', 'Документ')
                    preview = doc.page_content[:100].replace('\n', ' ')
                    print(f"   ✅ Найдено в: {source} (релевантность: {score:.2f})")
                    print(f"   📄 Фрагмент: {preview}...")
                else:
                    print("   ❌ Не найдено")
    else:
        print(f"\n❌ Папка с документами не найдена: {data_dir}")
        print("   Поместите файлы .txt в data/texts/")
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен!")

if __name__ == "__main__":
    test_knowledge_base()
