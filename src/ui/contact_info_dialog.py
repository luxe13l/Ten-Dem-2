"""Contact or group info dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.database.messages_db import get_media_gallery
from src.database.users_db import get_all_users
from src.styles.themes import get_theme_colors


class ContactInfoDialog(QDialog):
    def __init__(self, current_user, contact, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.contact = contact
        self.colors = get_theme_colors(getattr(current_user, "theme", "dark"))
        self.is_group = bool(getattr(contact, "is_group", False))
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Информация о группе" if self.is_group else "Информация о контакте")
        self.resize(460, 620 if self.is_group else 560)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {self.colors['bg_primary']}; color: {self.colors['text_primary']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-radius: 32px; }}")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(12)

        avatar = QLabel((self.contact.name or "?")[0].upper())
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(82, 82)
        avatar.setStyleSheet(
            f"QLabel {{ background-color: {self.colors['accent_primary']}; color: white; border-radius: 41px; font-size: 32px; font-weight: 700; }}"
        )
        hero_layout.addWidget(avatar, 0, Qt.AlignmentFlag.AlignHCenter)

        name = QLabel(self.contact.name or ("Группа" if self.is_group else "Пользователь"))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 25px; font-weight: 700;")
        hero_layout.addWidget(name)

        subtitle_text = f"@{getattr(self.contact, 'username', '')}" if getattr(self.contact, "username", "") else ("Групповой чат" if self.is_group else "username не указан")
        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 14px;")
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        cards = []
        if not self.is_group:
            cards.append(("Телефон", self.contact.phone or "не указан"))
            cards.append(("Статус", "в сети" if self.contact.status == "online" else "не в сети"))
        else:
            cards.append(("Тип", "Приватная группа"))
            cards.append(("Состоит", str(len(getattr(self.contact, "member_uids", []) or []))))
        cards.append(("О себе" if not self.is_group else "Описание", getattr(self.contact, "bio", "") or "пусто"))

        for title, value in cards:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-radius: 28px; }}")
            row = QVBoxLayout(card)
            row.setContentsMargins(18, 16, 18, 16)
            row.setSpacing(6)
            caption = QLabel(title)
            caption.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 12px;")
            row.addWidget(caption)
            text = QLabel(value)
            text.setWordWrap(True)
            text.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 15px; font-weight: 500;")
            row.addWidget(text)
            layout.addWidget(card)

        if self.is_group:
            members_card = QFrame()
            members_card.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-radius: 28px; }}")
            members_layout = QVBoxLayout(members_card)
            members_layout.setContentsMargins(18, 16, 18, 16)
            members_layout.setSpacing(8)
            title = QLabel("Состав")
            title.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 12px;")
            members_layout.addWidget(title)
            users_map = {user.get("uid"): user for user in get_all_users()}
            for member_uid in getattr(self.contact, "member_uids", []) or []:
                user = users_map.get(member_uid, {})
                member = QLabel(user.get("name", member_uid))
                member.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 14px;")
                members_layout.addWidget(member)
            layout.addWidget(members_card)

        photos = len(get_media_gallery(self.current_user.uid, self.contact.uid, "photo"))
        files = len(get_media_gallery(self.current_user.uid, self.contact.uid, "file"))
        media = QFrame()
        media.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-radius: 28px; }}")
        media_layout = QHBoxLayout(media)
        media_layout.setContentsMargins(18, 16, 18, 16)
        media_layout.setSpacing(12)
        for left, right in [("Фото", str(photos)), ("Файлы", str(files))]:
            block = QFrame()
            block.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_tertiary']}; border-radius: 24px; }}")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(14, 12, 14, 12)
            key = QLabel(left)
            key.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 12px;")
            val = QLabel(right)
            val.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 20px; font-weight: 700;")
            block_layout.addWidget(key)
            block_layout.addWidget(val)
            media_layout.addWidget(block, 1)
        layout.addWidget(media)
        layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 999px;
                padding: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {self.colors['bg_tertiary']}; }}
            """
        )
        layout.addWidget(close_btn)
