import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.schema import Document
    IMPORT_SUCCESS = True
except ImportError as e:
    logger.warning(f"Не удалось импортировать LangChain: {e}")
    logger.warning("Используется упрощенный режим без векторного поиска")
    IMPORT_SUCCESS = False

class SimpleKnowledgeBase:
    """Упрощенная база знаний для тестирования"""
    
    def __init__(self, persist_directory: str = None):
        """Инициализация упрощенной базы знаний"""
        if persist_directory is None:
            current_dir = Path(__file__).parent.parent.parent
            self.persist_directory = str(current_dir / "data" / "vector_db")
        else:
            self.persist_directory = persist_directory
        
        os.makedirs(self.persist_directory, exist_ok=True)
        self.documents = []
        self.load_existing_documents()
    
    def load_existing_documents(self):
        """Загружает существующие документы"""
        data_dir = Path(__file__).parent.parent.parent / "data" / "texts"
        if data_dir.exists():
            text_files = list(data_dir.glob("*.txt"))
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    if text.strip():
                        # Разбиваем текст на части (упрощенный вариант)
                        chunks = self.simple_split_text(text)
                        for i, chunk in enumerate(chunks):
                            self.documents.append({
                                "content": chunk,
                                "source": file_path.name,
                                "chunk": i,
                                "metadata": {"type": "law"}
                            })
                        logger.info(f"Загружено {len(chunks)} фрагментов из {file_path.name}")
                except Exception as e:
                    logger.error(f"Ошибка при чтении {file_path.name}: {e}")
        
        logger.info(f"Всего загружено {len(self.documents)} фрагментов")
    
    def simple_split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Простое разбиение текста на части"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            if end < text_length:
                # Пытаемся разбить по границе предложения
                for break_char in ['. ', '\n\n', '\n', ' ']:
                    break_pos = text.rfind(break_char, start, end)
                    if break_pos != -1:
                        end = break_pos + len(break_char)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Простой поиск по ключевым словам"""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            # Простой подсчет совпадений слов
            score = 0
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3 and word in content_lower:
                    score += 1
            
            if score > 0:
                # Создаем Document объект для совместимости
                langchain_doc = Document(
                    page_content=doc["content"],
                    metadata={
                        "source": doc["source"],
                        "chunk": doc["chunk"],
                        **doc.get("metadata", {})
                    }
                )
                # Нормализуем score
                normalized_score = min(score / len(query_words), 1.0) if query_words else 0
                results.append((langchain_doc, normalized_score))
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def get_document_count(self) -> int:
        """Возвращает количество документов"""
        return len(self.documents)
    
    def get_db_path(self) -> str:
        """Возвращает путь к БД"""
        return self.persist_directory

class AdvancedKnowledgeBase(SimpleKnowledgeBase):
    """Продвинутая база знаний с векторным поиском"""
    
    def __init__(self, persist_directory: str = None):
        if not IMPORT_SUCCESS:
            logger.warning("Библиотеки LangChain не установлены. Используется простой режим.")
            super().__init__(persist_directory)
            return
        
        if persist_directory is None:
            current_dir = Path(__file__).parent.parent.parent
            self.persist_directory = str(current_dir / "data" / "vector_db")
        else:
            self.persist_directory = persist_directory
        
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Инициализируем модель эмбеддингов
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Модель эмбеддингов инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели эмбеддингов: {e}")
            logger.warning("Перехожу в упрощенный режим")
            super().__init__(persist_directory)
            self.embeddings = None
            return
        
        self.vectorstore = None
        self._load_or_create_vectorstore()
    
    def _load_or_create_vectorstore(self):
        """Загружает или создает векторное хранилище"""
        try:
            if os.path.exists(os.path.join(self.persist_directory, "chroma.sqlite3")):
                logger.info(f"Загружаю векторную БД из {self.persist_directory}")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                count = self.vectorstore._collection.count()
                logger.info(f"Загружено {count} документов")
            else:
                logger.info("Векторная БД не найдена. Создам при первом поиске.")
        except Exception as e:
            logger.error(f"Ошибка при загрузке векторной БД: {e}")
            self.vectorstore = None
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Поиск с использованием векторной БД"""
        if self.vectorstore is None or self.embeddings is None:
            logger.warning("Векторная БД не доступна. Использую простой поиск.")
            return super().search(query, k)
        
        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Ошибка векторного поиска: {e}. Использую простой поиск.")
            return super().search(query, k)
    
    def create_vectorstore_from_documents(self):
        """Создает векторное хранилище из документов"""
        if self.embeddings is None:
            logger.error("Модель эмбеддингов не загружена")
            return False
        
        data_dir = Path(__file__).parent.parent.parent / "data" / "texts"
        if not data_dir.exists():
            logger.error(f"Директория с документами не найдена: {data_dir}")
            return False
        
        text_files = list(data_dir.glob("*.txt"))
        if not text_files:
            logger.error("Не найдено текстовых файлов")
            return False
        
        documents = []
        for file_path in text_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": file_path.name,
                            "file_path": str(file_path),
                            "type": "law"
                        }
                    )
                    documents.append(doc)
                    logger.info(f"Загружен: {file_path.name} ({len(text)} chars)")
            except Exception as e:
                logger.error(f"Ошибка при чтении {file_path.name}: {e}")
        
        if not documents:
            logger.error("Нет документов для обработки")
            return False
        
        # Разбиваем на чанки
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Создано {len(chunks)} фрагментов из {len(documents)} документов")
        
        # Создаем векторное хранилище
        try:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vectorstore.persist()
            logger.info(f"Векторная БД создана и сохранена в: {self.persist_directory}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании векторной БД: {e}")
            return False

# Автоматически выбираем подходящий класс
try:
    # Пытаемся использовать продвинутую версию
    KnowledgeBase = AdvancedKnowledgeBase
    logger.info("Используется продвинутая база знаний с векторным поиском")
except Exception as e:
    logger.warning(f"Не удалось инициализировать продвинутую базу: {e}")
    logger.info("Используется упрощенная база знаний")
    KnowledgeBase = SimpleKnowledgeBase

# Функция для тестирования
def test_knowledge_base():
    """Тестирование базы знаний"""
    print("🧪 Тестирование базы знаний...")
    print("=" * 60)
    
    kb = KnowledgeBase()
    print(f"📊 Загружено документов: {kb.get_document_count()}")
    print(f"📁 Путь к БД: {kb.get_db_path()}")
    
    if hasattr(kb, 'vectorstore') and kb.vectorstore is not None:
        print("✅ Используется векторный поиск")
    else:
        print("ℹ️ Используется простой поиск по ключевым словам")
    
    # Тестовые запросы
    test_queries = [
        "отпуск работника",
        "охрана труда",
        "рабочее время",
        "заработная плата"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Запрос: '{query}'")
        results = kb.search(query, k=2)
        
        if results:
            for i, (doc, score) in enumerate(results, 1):
                source = doc.metadata.get('source', 'Документ')
                preview = doc.page_content[:150].replace('\n', ' ')
                print(f"   {i}. [{source}] (релевантность: {score:.3f})")
                print(f"      {preview}...")
        else:
            print("   ❌ Ничего не найдено")
    
    print("\n" + "=" * 60)
    
    # Если это AdvancedKnowledgeBase и нет векторной БД, предложить создать
    if isinstance(kb, AdvancedKnowledgeBase) and kb.vectorstore is None:
        print("\n⚠️  Векторная БД не создана. Хотите создать?")
        print("   Запустите: python -c 'from app.ai.core import KnowledgeBase; kb = KnowledgeBase(); kb.create_vectorstore_from_documents()'")
    
    print("✅ Тест завершен!")

if __name__ == "__main__":
    test_knowledge_base()
