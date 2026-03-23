"""Contact row widget."""
from __future__ import annotations
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from src.styles import FONT_FAMILY
from src.styles.themes import get_theme_colors
from src.ui.avatar_widget import AvatarWidget
from src.utils.helpers import format_time, truncate

class ContactItem(QWidget):
    def __init__(self, user, last_message="", unread_count=0, timestamp=None, is_pinned=False, theme_name="dark", parent=None):
        super().__init__(parent)
        self.user = user
        self.last_message = last_message
        self.unread_count = unread_count
        self.timestamp = timestamp
        self.is_pinned = is_pinned
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self.is_selected = False  # Выбран ли чат сейчас
        self.unread_badge = None
        self.pin_icon = None
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        self.avatar = AvatarWidget(self.user.name, self.user.avatar_url, theme_name=self.theme_name)
        layout.addWidget(self.avatar)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        
        # ЗНАЧОК СКРЕПКИ ДЛЯ ЗАКРЕПЛЁННОГО ЧАТА
        if self.is_pinned:
            self.pin_icon = QLabel()
            self.pin_icon.setFixedSize(14, 14)
            self.pin_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pin_icon.setStyleSheet(f"color: {self.colors['accent_primary']}; font-size: 12px;")
            self.pin_icon.setText("📌")
            top_row.addWidget(self.pin_icon)
        
        self.name_label = QLabel(self.user.name)
        self.name_label.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.DemiBold))
        top_row.addWidget(self.name_label)
        top_row.addStretch()

        self.time_label = QLabel(format_time(self.timestamp) if self.timestamp else "")
        top_row.addWidget(self.time_label)
        info_layout.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)
        self.message_label = QLabel(truncate(self.last_message or "Нет сообщений", 36))
        self.message_label.setWordWrap(True)
        bottom_row.addWidget(self.message_label, 1)

        self.unread_badge = QLabel()
        self.unread_badge.setFixedSize(22, 22)
        self.unread_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unread_badge.setStyleSheet(
            "QLabel { background-color: #EF5A5A; color: white; border-radius: 11px; font-size: 11px; font-weight: 700; }"
        )
        bottom_row.addWidget(self.unread_badge)
        info_layout.addLayout(bottom_row)
        layout.addLayout(info_layout, 1)

        self.online_dot = QLabel()
        self.online_dot.setFixedSize(12, 12)
        layout.addWidget(self.online_dot)

        self.refresh_style()
        self.update_preview(self.last_message, self.timestamp, self.unread_count)
        self.update_status(self.user.status)

    def refresh_style(self):
        self.colors = get_theme_colors(self.theme_name)
        
        # ПОДСВЕТКА ВЫБРАННОГО ЧАТА
        if self.is_selected:
            card_bg = "rgba(108, 92, 231, 0.15)"  # Фиолетовый полупрозрачный
        elif self.is_pinned:
            card_bg = "rgba(68, 148, 74, 0.09)" if self.theme_name != "light" else "rgba(68, 148, 74, 0.10)"
        else:
            card_bg = "transparent"
        
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {card_bg};
                border-radius: 24px;
            }}
            QLabel {{
                background-color: transparent;
                border: none;
            }}
            """
        )
        self.name_label.setStyleSheet(f"color: {self.colors['text_primary']};")
        self.time_label.setStyleSheet(f"color: {self.colors['text_tertiary']}; font-size: 11px;")
        self.message_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 12px;")
        self.avatar.set_theme(self.theme_name)
        
        if self.pin_icon:
            self.pin_icon.setStyleSheet(f"color: {self.colors['accent_primary']}; font-size: 12px;")

    def set_selected(self, selected: bool):
        """Устанавливает состояние выделения чата"""
        self.is_selected = selected
        self.refresh_style()

    def update_preview(self, last_message="", timestamp=None, unread_count=0):
        self.last_message = last_message
        self.timestamp = timestamp
        self.unread_count = unread_count
        self.message_label.setText(truncate(self.last_message or "Нет сообщений", 36))
        self.time_label.setText(format_time(self.timestamp) if self.timestamp else "")
        self.unread_badge.setVisible(self.unread_count > 0)
        if self.unread_count > 0:
            self.unread_badge.setText(str(self.unread_count))

    def update_status(self, status):
        if status == "online":
            self.online_dot.setStyleSheet(
                f"QLabel {{ background-color: {self.colors['online']}; border: 2px solid {self.colors['bg_secondary']}; border-radius: 6px; }}"
            )
            self.online_dot.show()
        else:
            self.online_dot.hide()

    def sizeHint(self):
        return QSize(300, 84)