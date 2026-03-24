"""Database operations for users."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from src.database.firebase_client import get_db, get_firestore_client
from datetime import datetime
import uuid

# ================= БАЗОВЫЕ ФУНКЦИИ =================

def get_all_users():
    """Получает всех пользователей из базы."""
    db = get_db()
    if not db:
        return []
        
    users_ref = db.collection('users')
    try:
        docs = users_ref.stream()
        return [{**doc.to_dict(), 'uid': doc.id} for doc in docs]
    except Exception as e:
        print(f"❌ Ошибка получения списка пользователей: {e}")
        return []

def update_user(uid: str, data: Dict[str, Any]):
    """Обновляет данные пользователя по UID."""
    db = get_db()
    if not db:
        return False
        
    try:
        user_ref = db.collection('users').document(uid)
        user_ref.update(data)
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления пользователя {uid}: {e}")
        return False

def set_online_status(uid: str, status: str):
    """Устанавливает статус пользователя (online/offline)."""
    return update_user(uid, {'status': status})

def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """Получает пользователя по UID."""
    db = get_db()
    if not db:
        return None
    try:
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            return {**doc.to_dict(), 'uid': doc.id}
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя {uid}: {e}")
        return None

# ================= СОЗДАНИЕ И ПОИСК =================

def create_user(data: Dict[str, Any]) -> str:
    """Создает нового пользователя или возвращает ID существующего."""
    db = get_db()
    
    # Проверяем, нет ли уже пользователя с таким телефоном
    if 'phone' in data and data['phone']:
        existing = db.collection('users').where('phone', '==', data['phone']).limit(1).get()
        if existing:
            return existing[0].id

    uid = data.get('uid')
    if not uid:
        uid = f"user-{uuid.uuid4().hex[:12]}"
        data['uid'] = uid

    user_ref = db.collection('users').document(uid)
    user_ref.set(data)
    return uid

def find_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Ищет пользователя по номеру телефона. Возвращает данные или None."""
    db = get_db()
    if not phone:
        return None
    
    # ✅ Очищаем номер от всех нецифровых символов
    phone_digits = ''.join(filter(str.isdigit, phone))
    
    # ✅ Удаляем 7 или 8 в начале если есть
    if phone_digits.startswith('7'):
        phone_digits = phone_digits[1:]
    elif phone_digits.startswith('8'):
        phone_digits = phone_digits[1:]
    
    # ✅ Пробуем найти с 7 в начале (формат базы)
    try:
        query = db.collection('users').where('phone', '==', f"7{phone_digits}").limit(1).get()
        if query:
            doc = query[0]
            return {**doc.to_dict(), 'uid': doc.id}
    except Exception as e:
        print(f"⚠️ Ошибка поиска (формат 7): {e}")
    
    # ✅ Пробуем найти с +7 в начале
    try:
        query = db.collection('users').where('phone', '==', f"+7{phone_digits}").limit(1).get()
        if query:
            doc = query[0]
            return {**doc.to_dict(), 'uid': doc.id}
    except Exception as e:
        print(f"⚠️ Ошибка поиска (формат +7): {e}")
    
    # ✅ Пробуем найти с 8 в начале (старый формат)
    try:
        query = db.collection('users').where('phone', '==', f"8{phone_digits}").limit(1).get()
        if query:
            doc = query[0]
            return {**doc.to_dict(), 'uid': doc.id}
    except Exception as e:
        print(f"⚠️ Ошибка поиска (формат 8): {e}")
    
    return None

# ✅ ДОБАВЛЕНО: Алиас для совместимости со старым кодом
def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """То же самое что find_user_by_phone (для совместимости)."""
    return find_user_by_phone(phone)

# ================= КОНТАКТЫ =================

def add_contact_to_list(owner_uid: str, contact_data: Dict[str, Any]):
    """
    Добавляет контакт в список владельца.
    contact_data: {'uid': ..., 'name': ..., 'phone': ...}
    """
    db = get_db()
    if not db:
        return
    
    user_ref = db.collection('users').document(owner_uid)
    
    try:
        user_doc = user_ref.get()
        if not user_doc.exists:
            return

        data = user_doc.to_dict()
        contacts = data.get('contacts', [])
        
        # Проверка на дубликат
        exists = any(c.get('uid') == contact_data['uid'] for c in contacts)
        if not exists:
            new_contact = {
                'uid': contact_data['uid'],
                'name': contact_data.get('name', 'Unknown'),
                'phone': contact_data.get('phone', ''),
                'added_at': datetime.utcnow()
            }
            contacts.append(new_contact)
            user_ref.update({'contacts': contacts})
            print(f"✅ Контакт {contact_data.get('name')} добавлен в список {owner_uid}")
    except Exception as e:
        print(f"❌ Ошибка добавления контакта: {e}")

def get_contacts(user_uid: str) -> List[Dict[str, Any]]:
    """Получает список контактов пользователя."""
    db = get_db()
    if not db:
        return []
        
    try:
        user_ref = db.collection('users').document(user_uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return user_doc.to_dict().get('contacts', [])
        return []
    except Exception as e:
        print(f"❌ Ошибка получения контактов: {e}")
        return []