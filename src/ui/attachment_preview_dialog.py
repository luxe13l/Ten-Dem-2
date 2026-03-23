"""Simple confirmation dialog for attachments before sending."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout

from src.styles.themes import get_theme_colors


class AttachmentPreviewDialog(QDialog):
    def __init__(self, files: list[str], title: str = "Подтвердите отправку", parent=None):
        super().__init__(parent)
        self.files = files
        self.colors = get_theme_colors()
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.build_ui(title)

    def build_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        caption = QLabel(title)
        caption.setStyleSheet(
            f"color: {self.colors['text_primary']}; font-size: 18px; font-weight: 600;"
        )
        layout.addWidget(caption)

        subtitle = QLabel("Нажмите Enter или кнопку отправки, чтобы подтвердить. Esc отменит отправку.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(subtitle)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: 1px solid {self.colors['divider']};
                border-radius: 16px;
                padding: 8px;
            }}
            """
        )
        for file_path in self.files:
            self.list_widget.addItem(os.path.basename(file_path))
        layout.addWidget(self.list_widget)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {self.colors['text_secondary']};
                border: none;
                padding: 10px 12px;
            }}
            QPushButton:hover {{ color: {self.colors['text_primary']}; }}
            """
        )
        buttons.addWidget(cancel)

        confirm = QPushButton("Отправить")
        confirm.clicked.connect(self.accept)
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm.setDefault(True)
        confirm.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px 16px;
                font-weight: 600;
            }}
            """
        )
        buttons.addWidget(confirm)
        layout.addLayout(buttons)
