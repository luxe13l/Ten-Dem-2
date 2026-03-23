"""Theme-aware avatar widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.styles import FONT_FAMILY
from src.styles.themes import get_theme_colors


class AvatarWidget(QWidget):
    """Simple circular avatar with optional online indicator."""

    def __init__(self, name: str = "", avatar_url: str = "", size: int = 52, theme_name: str = "dark", parent=None):
        super().__init__(parent)
        self.name = name
        self.avatar_url = avatar_url
        self.size = size
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self.is_online = False
        self.label: QLabel | None = None
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(self.size, self.size)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel(self.get_initial())
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                color: {self.colors['text_primary']};
                font-size: {max(14, self.size // 3)}px;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            """
        )
        layout.addWidget(self.label)

    def _apply_style(self):
        self.colors = get_theme_colors(self.theme_name)
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {self.colors['bg_tertiary']};
                border-radius: {self.size // 2}px;
            }}
            """
        )

    def set_theme(self, theme_name: str):
        self.theme_name = theme_name or "dark"
        self._apply_style()
        if self.label:
            self.label.setStyleSheet(
                f"""
                QLabel {{
                    background: transparent;
                    color: {self.colors['text_primary']};
                    font-size: {max(14, self.size // 3)}px;
                    font-weight: 600;
                    font-family: {FONT_FAMILY};
                }}
                """
            )
        self.update()

    def get_initial(self) -> str:
        return self.name[0].upper() if self.name else "?"

    def set_online(self, is_online: bool):
        self.is_online = is_online
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.is_online:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        indicator_size = max(8, self.size // 5)
        painter.setBrush(QBrush(QColor(self.colors["online"])))
        painter.setPen(QPen(QColor(self.colors["bg_secondary"]), 2))
        painter.drawEllipse(
            self.width() - indicator_size - 2,
            self.height() - indicator_size - 2,
            indicator_size,
            indicator_size,
        )
        painter.end()
