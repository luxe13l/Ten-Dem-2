"""Firebase Client Initialization."""
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Глобальная переменная для хранения клиента базы данных
_db = None

def init_firebase():
    """
    Инициализирует Firebase при запуске приложения.
    Вызывается один раз в main.py.
    """
    global _db
    
    # Если уже инициализировано, просто возвращаем клиент
    if firebase_admin._apps:
        _db = firestore.client()
        return _db

    # Ищем ключ в корне проекта (Ten-Dem-3/firebase-key.json)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    key_path = os.path.join(project_root, "firebase-key.json")
    
    if not os.path.exists(key_path):
        key_path = "firebase-key.json"

    if not os.path.exists(key_path):
        raise FileNotFoundError(
            f"❌ Файл ключа Firebase не найден!\n"
            f"Ожидаемый путь: {key_path}\n"
            f"Положите файл 'firebase-key.json' в корень папки проекта."
        )

    print(f"🔑 Загрузка ключа Firebase: {key_path}")
    
    try:
        cred = credentials.Certificate(key_path)
        # ✅ Инициализируем с настройками для быстрого старта
        firebase_admin.initialize_app(cred, options={
            'httpTimeout': 5,  # Таймаут 5 секунд вместо бесконечности
            'connectTimeout': 3,
        })
        _db = firestore.client()
        print("✅ Firebase успешно инициализирован!")
        return _db
    except Exception as e:
        print(f"❌ Ошибка инициализации Firebase: {e}")
        raise e

def get_firestore_client():
    """
    Возвращает экземпляр клиента Firestore для использования в других модулях.
    """
    global _db
    if _db is None:
        try:
            return init_firebase()
        except Exception as e:
            print(f"⚠️ Попытка доступа к базе до инициализации: {e}")
            return None
    return _db

def get_db():
    """
    Возвращает экземпляр клиента Firestore (алиас для get_firestore_client).
    Нужно для совместимости со старым кодом.
    """
    return get_firestore_client()