import os
from pathlib import Path
from typing import List, Tuple
import logging
from .core import KnowledgeBase as BaseKnowledgeBase

logger = logging.getLogger(__name__)

class EnhancedKnowledgeBase(BaseKnowledgeBase):
    """Улучшенная база знаний с фильтрацией по типам документов."""
    
    def __init__(self, persist_directory: str = None):
        super().__init__(persist_directory)
        self.document_types = self._analyze_document_types()
    
    def _analyze_document_types(self):
        """Анализирует типы документов в базе."""
        types = {
            "tk_rf": "Трудовой кодекс РФ",
            "426_fz": "ФЗ №426 'О специальной оценке условий труда'",
            "2464_pp": "Постановление №2464 'Об обучении по ОТ'",
            "776n_prikaz": "Приказ №776н 'О СУОТ'",
            "772n_prikaz": "Приказ №772н 'О правилах и инструкциях'"
        }
        return types
    
    def search_by_type(self, query: str, doc_type: str = None, k: int = 5):
        """
        Поиск с фильтрацией по типу документа.
        
        Args:
            query: Поисковый запрос
            doc_type: Тип документа (tk_rf, 426_fz и т.д.)
            k: Количество результатов
        """
        all_results = self.search(query, k * 3)  # Берем больше, чтобы отфильтровать
        
        if doc_type:
            # Фильтруем по типу документа
            filtered = []
            for doc, score in all_results:
                source = doc.metadata.get('source', '').lower()
                if doc_type.lower() in source:
                    filtered.append((doc, score))
            
            # Если нашли по типу — возвращаем
            if filtered:
                return filtered[:k]
        
        # Иначе возвращаем все результаты
        return all_results[:k]
    
    def get_law_info(self, law_key: str):
        """Возвращает информацию о конкретном законе."""
        law_info = {
            "tk_rf": {
                "name": "Трудовой кодекс РФ",
                "description": "Основной закон, регулирующий трудовые отношения",
                "articles": ["212", "214", "219", "220"],
                "topics": ["отпуска", "рабочее время", "охрана труда", "зарплата"]
            },
            "426_fz": {
                "name": "Федеральный закон №426-ФЗ",
                "description": "О специальной оценке условий труда (СОУТ)",
                "articles": ["1", "3", "8", "15"],
                "topics": ["спецоценка", "вредные условия", "аттестация рабочих мест"]
            },
            "2464_pp": {
                "name": "Постановление №2464",
                "description": "О порядке обучения по охране труда",
                "articles": ["I", "II", "III"],
                "topics": ["обучение", "инструктаж", "проверка знаний"]
            }
        }
        
        return law_info.get(law_key, {"name": "Неизвестный документ"})
    
    def analyze_query(self, query: str):
        """
        Анализирует запрос и определяет, в каком законе вероятнее всего искать.
        
        Returns:
            dict: Информация о наиболее релевантных законах
        """
        query_lower = query.lower()
        
        # Ключевые слова для каждого закона
        keywords = {
            "tk_rf": ["отпуск", "рабочее время", "зарплата", "больничный", "увольнение",
                     "трудовой договор", "отпускные", "график работы"],
            "426_fz": ["соут", "специальная оценка", "вредные условия", "аттестация",
                      "рабочее место", "компенсации", "льготы"],
            "2464_pp": ["обучение", "инструктаж", "проверка знаний", "курсы",
                       "программа обучения", "вводный инструктаж"],
            "776n_prikaz": ["суот", "система управления", "политика", "процедуры",
                          "мониторинг", "аудит", "управление рисками"],
            "772n_prikaz": ["инструкция", "правила", "разработка", "содержание",
                          "утверждение", "пересмотр", "ознакомление"]
        }
        
        # Подсчет совпадений
        scores = {}
        for law, words in keywords.items():
            score = sum(1 for word in words if word in query_lower)
            if score > 0:
                scores[law] = score
        
        # Сортируем по релевантности
        sorted_laws = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "query": query,
            "suggested_laws": sorted_laws[:3],  # Топ-3 наиболее релевантных
            "total_matches": sum(scores.values())
        }

# Глобальный экземпляр для использования в боте
knowledge_base = EnhancedKnowledgeBase()

def get_knowledge_base():
    """Возвращает глобальный экземпляр базы знаний."""
    return knowledge_base
