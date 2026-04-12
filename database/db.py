# database/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
#from dotenv import load_dotenv

#load_dotenv()

# Используем новую базу данных
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:toor@doterrabot-db-bup2tl:5432/doterra_bot')

if 'sqlite' in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы в базе данных doterra_bot")
    
    db = SessionLocal()
    try:
        from database.models import SystemSettings, ProductDictionary
        
        # Добавляем системные настройки
        settings = [
            {"key": "rag_top_k", "value": "5", "description": "Количество чанков для RAG"},
            {"key": "rag_confidence_threshold", "value": "0.6", "description": "Порог уверенности RAG"},
            {"key": "max_expert_iterations", "value": "2", "description": "Максимум итераций эксперта"},
        ]
        
        for setting in settings:
            existing = db.query(SystemSettings).filter_by(key=setting["key"]).first()
            if not existing:
                db.add(SystemSettings(**setting))
        
        # Добавляем продукты doTERRA
        products = [
            {"name_en": "Lavender", "name_ru": "Лаванда", "category": "успокаивающие"},
            {"name_en": "On Guard", "name_ru": "Он Гард", "category": "иммунитет"},
            {"name_en": "Peppermint", "name_ru": "Перечная мята", "category": "энергия"},
            {"name_en": "Tea Tree", "name_ru": "Чайное дерево", "category": "кожа"},
            {"name_en": "Lemon", "name_ru": "Лимон", "category": "детокс"},
            {"name_en": "Frankincense", "name_ru": "Ладан", "category": "клеточное здоровье"},
            {"name_en": "Oregano", "name_ru": "Орегано", "category": "иммунитет"},
            {"name_en": "Deep Blue", "name_ru": "Дип Блю", "category": "мышцы и суставы"},
            {"name_en": "Breathe", "name_ru": "Бриз", "category": "дыхание"},
            {"name_en": "DigestZen", "name_ru": "ДижестЗен", "category": "пищеварение"},
            {"name_en": "Serenity", "name_ru": "Серенити", "category": "сон"},
            {"name_en": "Wild Orange", "name_ru": "Дикий апельсин", "category": "настроение"},
        ]
        
        for product in products:
            existing = db.query(ProductDictionary).filter_by(name_en=product["name_en"]).first()
            if not existing:
                db.add(ProductDictionary(**product))
        
        db.commit()
        print("✅ Начальные данные добавлены (услуги, настройки)")
        
    except Exception as e:
        print(f"⚠️ Ошибка добавления начальных данных: {e}")
        db.rollback()
    finally:
        db.close()
