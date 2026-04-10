# bot/yandexgpt_client.py
import os
import logging
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


class YandexGPTClient:
    """Клиент для работы с YandexGPT API"""
    
    def __init__(self):
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.model = os.getenv('YANDEX_MODEL', 'yandexgpt-lite')
        self.mock_mode = os.getenv('RAG_MOCK_MODE', 'false').lower() == 'true'
        
        if self.mock_mode:
            logging.info("🔧 YandexGPT работает в МОК-режиме")
            self.available = True
        elif not self.folder_id or not self.api_key:
            logging.error("YANDEX_FOLDER_ID или YANDEX_API_KEY не заданы")
            self.available = False
        else:
            self.available = True
            logging.info(f"✅ YandexGPT клиент настроен (folder_id: {self.folder_id})")
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        temperature: float = 0.6,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """Генерация ответа через YandexGPT"""
        
        if not self.available:
            return None
        
        # Мок-режим для тестирования
        if self.mock_mode:
            return self._get_mock_answer(prompt)
        
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        # ПРАВИЛЬНЫЕ ЗАГОЛОВКИ - как в тесте!
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {self.api_key}',  # ← Ключевой момент!
            'x-folder-id': self.folder_id
        }
        
        # Формируем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": messages
        }
        
        try:
            logging.info("📤 Отправка запроса к YandexGPT...")
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text', '')
                logging.info("✅ Ответ получен")
                return answer
            else:
                logging.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")
            return None
    
    def _get_mock_answer(self, prompt: str) -> str:
        """Мок-ответ для тестирования"""
        prompt_lower = prompt.lower()
        
        if any(w in prompt_lower for w in ['иммун', 'on guard', 'защит']):
            return """
1. Краткий вывод: Для укрепления иммунитета рекомендуется использовать эфирные масла с антибактериальными свойствами.

2. Рекомендуемые продукты:
   - Он Гард (On Guard) - защитная смесь масел
   - Орегано (Oregano) - природный антибиотик
   - Лимон (Lemon) - для детоксикации

3. Способ применения:
   - Наносить 1-2 капли на стопы утром и вечером
   - Добавлять 2-3 капли в диффузор

4. Меры предосторожности:
   - Орегано разбавлять маслом-носителем

⚠️ Перед применением проконсультируйтесь с врачом.
"""
        
        if any(w in prompt_lower for w in ['сон', 'бессон', 'спать', 'стресс']):
            return """
1. Краткий вывод: Для улучшения сна рекомендуются успокаивающие эфирные масла.

2. Рекомендуемые продукты:
   - Лаванда (Lavender) - основное масло для сна
   - Серенити (Serenity) - успокаивающая смесь

3. Способ применения:
   - 3-5 капель в диффузор за 30 минут до сна
   - Нанести 1-2 капли на подушку

4. Меры предосторожности:
   - Не превышать дозировку

⚠️ Перед применением проконсультируйтесь с врачом.
"""
        
        return """
1. Краткий вывод: Эфирные масла doTERRA могут быть эффективны для поддержания здоровья.

2. Рекомендуемые продукты:
   - Лаванда (Lavender) - успокаивающее
   - Лимон (Lemon) - для энергии
   - Перечная мята (Peppermint) - для бодрости

3. Способ применения:
   - Ароматерапия: 3-5 капель в диффузор
   - Местное применение: 1-2 капли с маслом-носителем

4. Меры предосторожности:
   - Избегать попадания в глаза
   - Провести тест на чувствительность

⚠️ Перед применением проконсультируйтесь с врачом.
"""


# Создаем глобальный экземпляр
yandex_client = YandexGPTClient()