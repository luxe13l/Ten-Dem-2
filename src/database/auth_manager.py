"""Authentication and registration helpers."""

from __future__ import annotations

from datetime import datetime
import random
import re
import uuid

from src.database.firebase_client import get_db
from src.database.users_db import get_all_users, update_user


class AuthManager:
    def __init__(self):
        self.current_user = None
        self._temp_codes: dict[str, dict] = {}

    def send_verification_code(self, phone):
        try:
            code = str(random.randint(100000, 999999))
            verification_id = f"test_{phone}_{datetime.now().timestamp()}"
            self._temp_codes[verification_id] = {
                "phone": phone,
                "code": code,
                "created": datetime.now(),
            }
            print(f"Код для {phone}: {code}")
            return True, "Код отправлен", verification_id
        except Exception as exc:
            return False, f"Ошибка отправки кода: {exc}", ""

    def verify_code(self, verification_id, code):
        try:
            stored = self._temp_codes.get(verification_id)
            if not stored:
                return False, "Неверный код верификации", ""
            if (datetime.now() - stored["created"]).total_seconds() > 300:
                return False, "Код истёк", ""
            if len(code) != 6 or not code.isdigit():
                return False, "Код должен содержать 6 цифр", ""
            phone = stored["phone"]
            del self._temp_codes[verification_id]
            return True, "Код подтверждён", phone
        except Exception as exc:
            return False, f"Ошибка проверки кода: {exc}", ""

    @staticmethod
    def normalize_username(username: str) -> str:
        return (username or "").strip().lower().lstrip("@")

    def validate_username(self, username: str):
        normalized = self.normalize_username(username)
        if len(normalized) < 3 or len(normalized) > 20:
            return False, "Username должен быть от 3 до 20 символов"
        if any(char.isdigit() for char in normalized):
            return False, "Цифры в username использовать нельзя"
        if not re.fullmatch(r"[a-z_]+", normalized):
            return False, "Только латинские буквы и подчёркивание"
        if normalized.startswith("_") or normalized.endswith("_"):
            return False, "Username не должен начинаться или заканчиваться _"
        return True, normalized

    def check_username_available(self, username, exclude_uid: str = ""):
        try:
            valid, result = self.validate_username(username)
            if not valid:
                return False, result

            normalized = result
            db = get_db()
            if db:
                try:
                    docs = db.collection("users").where("username", "==", normalized).limit(2).stream()
                    for doc in docs:
                        if exclude_uid and doc.id == exclude_uid:
                            continue
                        return False, "Этот username уже занят"
                except Exception as exc:
                    print(f"Ошибка проверки username в Firebase: {exc}")

            for user in get_all_users():
                if self.normalize_username(user.get("username", "")) == normalized and user.get("uid") != exclude_uid:
                    return False, "Этот username уже занят"
            return True, normalized
        except Exception as exc:
            print(f"Критическая ошибка проверки username: {exc}")
            return False, "Не удалось проверить username"

    def create_user_profile(self, phone, name, surname, username):
        available, result = self.check_username_available(username)
        if not available:
            return False, "", result

        username = result
        uid = f"user-{uuid.uuid4().hex[:12]}"
        user_data = {
            "uid": uid,
            "phone": phone,
            "name": name,
            "surname": surname,
            "username": username,
            "full_name": f"{name} {surname}".strip(),
            "avatar_url": "",
            "status": "online",
            "last_seen": datetime.now(),
            "theme": "dark",
            "bio": "",
            "created_at": datetime.now(),
        }

        db = get_db()
        if db:
            try:
                db.collection("users").document(uid).set(user_data)
            except Exception as exc:
                print(f"Ошибка создания пользователя в Firebase: {exc}")

        update_user(uid, user_data)
        self.current_user = user_data
        return True, uid, "Профиль создан"

    def get_user_by_phone(self, phone):
        normalized_phone = re.sub(r"\D", "", phone or "")
        for user in get_all_users():
            if re.sub(r"\D", "", user.get("phone", "")) == normalized_phone:
                return user
        return None

    def set_current_user(self, user_data):
        self.current_user = user_data

    def get_current_user(self):
        return self.current_user


auth_manager = AuthManager()
