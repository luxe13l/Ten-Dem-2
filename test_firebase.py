# test_firebase.py
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== ТЕСТ FIREBASE ===")
print(f"Текущая папка: {os.getcwd()}")
print(f"firebase-key.json существует: {os.path.exists('firebase-key.json')}")

try:
    from src.database.firebase_client import init_firebase, get_db
    
    print("\n1. Инициализация Firebase...")
    db = init_firebase()
    
    if db is None:
        print("❌ ОШИБКА: Firebase не инициализирован")
        print("Проверь что firebase-key.json в корне проекта и имеет правильные права")
        sys.exit(1)
    
    print("✅ Firebase подключен!")
    
    # Пробуем получить пользователей
    print("\n2. Тест получения пользователей...")
    users_ref = db.collection('users')
    users = users_ref.limit(3).stream()
    
    count = 0
    for user in users:
        data = user.to_dict()
        print(f"  - ID: {user.id}")
        print(f"    Name: {data.get('name', 'N/A')}")
        print(f"    Phone: {data.get('phone', 'N/A')}")
        count += 1
    
    if count == 0:
        print("  (база пустая - это нормально для нового проекта)")
    
    # Пробуем создать тестового пользователя
    print("\n3. Тест создания пользователя...")
    from datetime import datetime
    test_data = {
        'phone': '+79990000000',
        'name': 'Test User',
        'avatar_url': '',
        'status': 'online',
        'last_seen': datetime.now()
    }
    
    doc_ref = users_ref.add(test_data)
    print(f"  ✅ Создан пользователь с ID: {doc_ref[1].id}")
    
    print("\n=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ ===")
    
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА: {e}")
    print("Проверь что в папках есть __init__.py файлы")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()