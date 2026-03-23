"""Firebase initialization helpers."""
from __future__ import annotations

import os

import firebase_admin
from firebase_admin import credentials, firestore


_db_client = None
_init_attempted = False


def init_firebase():
    """Initialize Firebase Admin SDK once."""
    global _db_client, _init_attempted

    if _init_attempted:
        return _db_client
    _init_attempted = True

    try:
        key_path = os.getenv("FIREBASE_KEY_PATH") or os.path.join(
            os.path.dirname(__file__), "..", "..", "firebase-key.json"
        )
        key_path = os.path.abspath(key_path)
        print(f"Поиск ключа Firebase: {key_path}")

        if not os.path.exists(key_path):
            print(f"Файл ключа Firebase не найден: {key_path}")
            return None

        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("Firebase успешно инициализирован")

        _db_client = firestore.client()
        return _db_client
    except Exception as exc:
        print(f"Ошибка инициализации Firebase: {exc}")
        return None


def get_db():
    global _db_client
    if _db_client is None:
        _db_client = init_firebase()
    return _db_client
