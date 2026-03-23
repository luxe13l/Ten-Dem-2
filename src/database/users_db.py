"""User storage with Firestore support and local fallback."""

from __future__ import annotations

from datetime import datetime

from src.database.firebase_client import get_db
from src.database.local_store import load_store, save_store


def get_user_by_phone(phone):
    db = get_db()
    if db is not None:
        try:
            docs = db.collection("users").where("phone", "==", phone).limit(1).stream()
            for doc in docs:
                return {"uid": doc.id, **(doc.to_dict() or {})}
        except Exception as exc:
            print(f"Ошибка получения пользователя из Firebase: {exc}")

    users = load_store().get("users", {})
    for uid, data in users.items():
        if data.get("phone") == phone:
            return {"uid": uid, **data}
    return None


def create_user(user_data):
    uid = user_data.get("uid") or f"user-{int(datetime.now().timestamp())}"
    payload = {**user_data, "uid": uid}

    db = get_db()
    if db is not None:
        try:
            db.collection("users").document(uid).set(payload)
        except Exception as exc:
            print(f"Ошибка создания пользователя в Firebase: {exc}")

    store = load_store()
    store.setdefault("users", {})[uid] = payload
    save_store(store)
    return uid


def update_user(uid, data):
    db = get_db()
    if db is not None:
        try:
            db.collection("users").document(uid).set(data, merge=True)
        except Exception as exc:
            print(f"Ошибка обновления пользователя в Firebase: {exc}")

    store = load_store()
    store.setdefault("users", {})
    current = store["users"].get(uid, {"uid": uid})
    current.update(data)
    current["uid"] = uid
    store["users"][uid] = current
    save_store(store)
    return True


def get_all_users():
    db = get_db()
    if db is not None:
        try:
            docs = db.collection("users").stream()
            return [{"uid": doc.id, **(doc.to_dict() or {})} for doc in docs]
        except Exception as exc:
            print(f"Ошибка получения пользователей из Firebase: {exc}")
    return list(load_store().get("users", {}).values())


def set_online_status(uid, status):
    return update_user(uid, {"status": status, "last_seen": datetime.now()})
