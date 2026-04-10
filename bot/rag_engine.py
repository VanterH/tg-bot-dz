# bot/rag_engine.py
import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
from bot.yandexgpt_client import yandex_client

load_dotenv()
logging.basicConfig(level=logging.INFO)


class RAGEngine:
    """RAG движок для формирования предварительных ответов"""
    
    def __init__(self):
        self.top_k = int(os.getenv('RAG_TOP_K', 5))
        self.confidence_threshold = float(os.getenv('RAG_CONFIDENCE_THRESHOLD', 0.6))
        logging.info(f"RAG Engine initialized (top_k={self.top_k})")
    
    async def search_knowledge_base(self, question: str) -> List[Dict]:
        """Поиск в базе знаний"""
        from database.db import SessionLocal
        from database.models import KnowledgeBase
        
        session = SessionLocal()
        chunks = []
        
        try:
            # Простой поиск по ключевым словам
            keywords = question.lower().split()[:10]
            all_chunks = session.query(KnowledgeBase).all()
            
            for chunk in all_chunks:
                chunk_text = chunk.text.lower()
                score = sum(1 for kw in keywords if len(kw) > 3 and kw in chunk_text)
                
                if score > 0:
                    chunks.append({
                        "id": chunk.kb_id,
                        "text": chunk.text,
                        "source": chunk.source,
                        "score": score
                    })
            
            chunks.sort(key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            logging.error(f"Search error: {e}")
        
        session.close()
        return chunks[:self.top_k]
    
    async def generate_answer(
        self, 
        question: str, 
        user_id: int, 
        expert_feedback: str = None
    ) -> Dict[str, Any]:
        """Генерация предварительного ответа"""
        
        # 1. Поиск в БЗ
        relevant_chunks = await self.search_knowledge_base(question)
        
        # 2. Формируем контекст
        context = ""
        sources = []
        for chunk in relevant_chunks:
            context += chunk.get('text', '') + "\n\n"
            if chunk.get('source'):
                sources.append(chunk.get('source'))
        
        # 3. Формируем промпт
        if expert_feedback:
            context += f"\nУточнение эксперта: {expert_feedback}\n"
        
        system_prompt = """Ты — сертифицированный консультант doTERRA.

Правила:
1. Отвечай ТОЛЬКО на основе предоставленной информации
2. Не ставь медицинские диагнозы
3. Указывай конкретные продукты doTERRA
4. Обязательно добавь предупреждение о консультации с врачом

Формат ответа:
1. Краткий вывод
2. Рекомендуемые продукты
3. Способ применения
4. Меры предосторожности"""

        user_prompt = f"""
=== ВОПРОС ПОЛЬЗОВАТЕЛЯ ===
{question}

=== ИНФОРМАЦИЯ ИЗ БАЗЫ ЗНАНИЙ ===
{context if context else "Информация отсутствует."}

Сформируй ответ по правилам выше.
"""
        
        # 4. Вызов YandexGPT
        raw_answer = await yandex_client.generate(user_prompt, system_prompt, temperature=0.3)
        
        if not raw_answer:
            return {
                "answer": "❌ Сервис временно недоступен. Вопрос передан эксперту.",
                "confidence": 0.0,
                "sources": sources,
                "needs_clarification": True
            }
        
        # 5. Проверка на уточнение
        needs_clarification = any(word in raw_answer.lower() for word in 
            ['не нашел', 'недостаточно', 'отсутствует', 'нет информации'])
        
        confidence = 0.7 if not needs_clarification and sources else 0.3
        
        return {
            "answer": raw_answer,
            "confidence": confidence,
            "sources": sources[:3],
            "needs_clarification": needs_clarification
        }


rag_engine = RAGEngine()