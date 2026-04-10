# test_api_direct.py - Прямой тест API-ключа
import requests
import json

# ============ НАСТРОЙКИ (ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ) ============
FOLDER_ID = ""  # Ваш folder_id
API_KEY = ""  # Ваш API-ключ (начинается с AQVN)
# =============================================================

def test_yandex_gpt():
    print("="*50)
    print("ПРЯМОЙ ТЕСТ YANDEXGPT API")
    print("="*50)
    
    print(f"\n📡 Folder ID: {FOLDER_ID}")
    print(f"🔑 API Key: {API_KEY[:20]}...{API_KEY[-10:] if len(API_KEY) > 20 else ''}")
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Заголовки - ключевой момент!
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}",  # ← ПРАВИЛЬНО: Api-Key, не Bearer!
        "x-folder-id": FOLDER_ID
    }
    
    # Тело запроса
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 500
        },
        "messages": [
            {
                "role": "user",
                "text": "Какое эфирное масло doTERRA помогает при бессоннице?"
            }
        ]
    }
    
    print("\n📤 Отправка запроса...")
    print(f"   URL: {url}")
    print(f"   Headers: {json.dumps(headers, indent=2)}")
    print(f"   Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"\n📥 Ответ:")
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text', '')
            print(f"\n✅ УСПЕХ! Ответ получен:")
            print(f"\n📝 {answer}")
        else:
            print(f"\n❌ ОШИБКА: {response.text}")
            
    except Exception as e:
        print(f"\n❌ ИСКЛЮЧЕНИЕ: {e}")

if __name__ == "__main__":
    test_yandex_gpt()