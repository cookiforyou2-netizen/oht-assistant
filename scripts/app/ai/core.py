import os
from pathlib import Path
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

class KnowledgeBase:
    """Класс для работы с базой знаний документов по охране труда."""
    
    def __init__(self, persist_directory: str = None):
        """
        Инициализация базы знаний.
        
        Args:
            persist_directory: Директория для сохранения векторной БД.
                              Если None, используется data/vector_db/
        """
        if persist_directory is None:
            # Путь относительно корня проекта
            current_dir = Path(__file__).parent.parent.parent
            self.persist_directory = str(current_dir / "data" / "vector_db")
        else:
            self.persist_directory = persist_directory
        
        # Создаем директорию, если она не существует
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Инициализируем модель для эмбеддингов (векторных представлений текста)
        # 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' хорошо работает с русским
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},  # Используем CPU для совместимости
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Инициализируем векторное хранилище
        self.vectorstore = None
        self._load_existing_db()
    
    def _load_existing_db(self):
        """Загружает существующую базу данных, если она есть."""
        try:
            # Проверяем, есть ли уже сохраненная база
            if os.path.exists(os.path.join(self.persist_directory, "chroma.sqlite3")):
                print(f"📂 Загружаю существующую базу знаний из {self.persist_directory}")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print(f"✅ Загружено документов: {self.vectorstore._collection.count()}")
            else:
                print("🆕 База знаний не найдена, будет создана новая.")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить существующую базу: {e}")
            print("Создаю новую базу знаний...")
    
    def load_documents(self, file_paths: List[Path]):
        """
        Загружает документы из файлов и добавляет их в базу знаний.
        
        Args:
            file_paths: Список путей к текстовым файлам.
        """
        documents = []
        
        for file_path in file_paths:
            try:
                print(f"📖 Читаю файл: {file_path.name}")
                
                # Читаем текстовый файл
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if not text.strip():
                    print(f"  ⚠️ Файл {file_path.name} пуст, пропускаю.")
                    continue
                
                # Создаем документ LangChain с метаданными
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "type": "law"  # Тип документа: закон, инструкция и т.д.
                    }
                )
                documents.append(doc)
                print(f"  ✅ Загружено: {len(text)} символов")
                
            except Exception as e:
                print(f"  ❌ Ошибка при чтении {file_path.name}: {e}")
        
        if not documents:
            print("❌ Нет документов для обработки.")
            return
        
        # Разбиваем документы на чанки (фрагменты)
        print("\n✂️ Разбиваю документы на фрагменты...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # Размер фрагмента в символах
            chunk_overlap=200,    # Перекрытие между фрагментами
            separators=["\n\n", "\n", " ", ""]  # Приоритеты разделения
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✅ Создано {len(chunks)} фрагментов из {len(documents)} документов.")
        
        # Создаем или обновляем векторное хранилище
        if self.vectorstore is None:
            print("🆕 Создаю новую векторную базу...")
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        else:
            print("🔄 Добавляю документы в существующую базу...")
            # Здесь можно добавить логику для обновления существующей базы
            # Пока просто пересоздаем для простоты
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
        
        # Сохраняем базу на диск
        self.vectorstore.persist()
        print(f"💾 База сохранена в: {self.persist_directory}")
    
    def search(self, query: str, k: int = 5) -> List:
        """
        Ищет наиболее релевантные фрагменты по запросу.
        
        Args:
            query: Поисковый запрос.
            k: Количество возвращаемых результатов.
            
        Returns:
            Список кортежей (документ, оценка релевантности).
        """
        if self.vectorstore is None:
            print("❌ База знаний не загружена. Сначала загрузите документы.")
            return []
        
        try:
            # Ищем k наиболее релевантных фрагментов
            results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return []
    
    def get_db_path(self) -> str:
        """Возвращает путь к директории с векторной БД."""
        return self.persist_directory
    
    def get_document_count(self) -> int:
        """Возвращает количество документов в базе."""
        if self.vectorstore is None:
            return 0
        try:
            return self.vectorstore._collection.count()
        except:
            return 0

# Для простоты тестирования
if __name__ == "__main__":
    print("🧪 Тестирование модуля KnowledgeBase...")
    
    # Пример использования
    kb = KnowledgeBase()
    
    # Путь к тестовому документу
    test_doc = Path(__file__).parent.parent.parent / "data" / "texts" / "Трудовой кодекс РФ.txt"
    
    if test_doc.exists():
        kb.load_documents([test_doc])
        
        # Тестовый поиск
        test_query = "охрана труда"
        print(f"\n🔍 Тестовый поиск: '{test_query}'")
        results = kb.search(test_query, k=2)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n{i}. [Сходство: {score:.3f}]")
            print(f"   Источник: {doc.metadata.get('source', 'Неизвестно')}")
            print(f"   Текст: {doc.page_content[:150]}...")
    else:
        print(f"❌ Тестовый документ не найден: {test_doc}")
        print("Поместите файл 'Трудовой кодекс РФ.txt' в data/texts/")
