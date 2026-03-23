# src/auth/login_manager.py
# -*- coding: utf-8 -*-

"""
Модуль управления входом через Firestore (Admin SDK).
Вход выполняется по номеру телефона: если пользователь существует — возвращаем его,
иначе создаём нового в коллекции users.
"""

import uuid
from datetime import datetime

from database.users_db import UsersDB
from models.user import User


class LoginManager:
    """Класс для входа/регистрации пользователя через Firestore."""

    @staticmethod
    def login_or_register(phone: str, name: str = "") -> User:
        """
        Выполняет вход или регистрацию по номеру телефона.
        Если пользователь с таким телефоном уже есть — обновляет статус и возвращает его.
        Если нет — создаёт нового пользователя.

        Args:
            phone (str): номер телефона (в формате +7...).
            name (str, optional): имя пользователя (будет использовано при создании).

        Returns:
            User: объект пользователя.
        """
        # Ищем существующего пользователя по телефону
        user = UsersDB.get_user_by_phone(phone)
        if user:
            # Обновляем статус и last_seen
            user.status = "online"
            user.last_seen = datetime.now()
            UsersDB.update_user(user.uid, {
                "status": user.status,
                "last_seen": user.last_seen
            })
            return user

        # Создаём нового пользователя
        uid = str(uuid.uuid4())  # или можно использовать phone как uid? лучше генерировать
        new_user = User(
            uid=uid,
            phone=phone,
            name=name if name else f"User_{phone[-4:]}",  # имя по умолчанию
            avatar_url="",
            status="online",
            last_seen=datetime.now()
        )
        UsersDB.create_user({
            "phone": new_user.phone,
            "name": new_user.name,
            "avatar_url": new_user.avatar_url,
            "status": new_user.status,
            "last_seen": new_user.last_seen
        })
        return new_user