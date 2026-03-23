"""User model."""

from __future__ import annotations

from datetime import datetime, timedelta


class User:
    def __init__(
        self,
        uid,
        phone,
        name,
        avatar_url="",
        status="offline",
        last_seen=None,
        username="",
        surname="",
        bio="",
        theme="dark",
        is_group=False,
        member_uids=None,
    ):
        self.uid = uid
        self.phone = phone
        self.name = name
        self.avatar_url = avatar_url
        self.status = status
        self.last_seen = last_seen or datetime.now()
        self.username = username
        self.surname = surname
        self.bio = bio
        self.theme = theme
        self.is_group = bool(is_group)
        self.member_uids = list(member_uids or [])

    def to_dict(self):
        return {
            "phone": self.phone,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "status": self.status,
            "last_seen": self.last_seen,
            "username": self.username,
            "surname": self.surname,
            "bio": self.bio,
            "theme": self.theme,
            "is_group": self.is_group,
            "member_uids": self.member_uids,
        }

    @staticmethod
    def from_dict(data, doc_id=None):
        try:
            last_seen = data.get("last_seen")
            if last_seen and hasattr(last_seen, "to_pydatetime"):
                last_seen = last_seen.to_pydatetime()
            return User(
                uid=doc_id or data.get("uid", ""),
                phone=data.get("phone", ""),
                name=data.get("name", ""),
                avatar_url=data.get("avatar_url", ""),
                status=data.get("status", "offline"),
                last_seen=last_seen,
                username=data.get("username", ""),
                surname=data.get("surname", ""),
                bio=data.get("bio", ""),
                theme=data.get("theme", "dark"),
                is_group=bool(data.get("is_group", False)),
                member_uids=data.get("member_uids", []) or [],
            )
        except Exception:
            return User(uid="", phone="", name="Неизвестный")

    def get_online_status(self):
        try:
            if self.status == "online":
                return "в сети"
            if not self.last_seen:
                return "был давно"
            if datetime.now() - self.last_seen < timedelta(minutes=5):
                return "был недавно"
            return f"был {self.last_seen.strftime('%d.%m %H:%M')}"
        except Exception:
            return "offline"

    def __str__(self):
        return self.name
