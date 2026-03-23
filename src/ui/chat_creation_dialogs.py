"""Dialogs for creating contacts and groups."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.styles.themes import get_theme_colors


def looks_like_real_name(value: str) -> bool:
    cleaned = (value or "").strip()
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁё -]{2,40}", cleaned):
        return False
    letters = re.sub(r"[^A-Za-zА-Яа-яЁё]", "", cleaned).lower()
    if len(set(letters)) < 2:
        return False
    if re.search(r"(.)\1\1", letters):
        return False
    vowels = "aeiouyауоыиэяюёе"
    return any(ch in vowels for ch in letters)


class CreateContactDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = get_theme_colors()
        self.payload = None
        self.setModal(True)
        self.setWindowTitle("Создать контакт")
        self.resize(360, 260)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Новый контакт")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        self.name_input.setStyleSheet(self._input_style())
        layout.addWidget(self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7XXXXXXXXXX")
        self.phone_input.setStyleSheet(self._input_style())
        layout.addWidget(self.phone_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        cancel.setStyleSheet(self._secondary_button())
        buttons.addWidget(cancel)
        create = QPushButton("Создать")
        create.clicked.connect(self.submit)
        create.setStyleSheet(self._primary_button())
        buttons.addWidget(create)
        layout.addLayout(buttons)

    def submit(self):
        name = self.name_input.text().strip()
        phone = re.sub(r"\D", "", self.phone_input.text())
        if not name or not phone:
            self.error_label.setText("Имя и номер обязательны")
            return
        if not looks_like_real_name(name):
            self.error_label.setText("Имя выглядит некорректно")
            return
        if len(phone) != 11:
            self.error_label.setText("Введите корректный номер")
            return
        self.payload = {"name": name, "phone": f"+{phone}"}
        self.accept()

    def _input_style(self):
        return f"QLineEdit {{ background-color: {self.colors['bg_tertiary']}; color: {self.colors['text_primary']}; border: none; border-radius: 16px; padding: 12px 14px; }}"

    def _primary_button(self):
        return f"QPushButton {{ background-color: {self.colors['accent_primary']}; color: white; border: none; border-radius: 14px; padding: 10px 14px; font-weight: 600; }}"

    def _secondary_button(self):
        return f"QPushButton {{ background-color: transparent; color: {self.colors['text_secondary']}; border: none; border-radius: 14px; padding: 10px 14px; }}"


class CreateGroupDialog(QDialog):
    def __init__(self, users: list[dict], parent=None):
        super().__init__(parent)
        self.users = users
        self.colors = get_theme_colors()
        self.payload = None
        self.setModal(True)
        self.setWindowTitle("Создать группу")
        self.resize(420, 520)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Новая группа")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название группы")
        self.name_input.setStyleSheet(self._input_style())
        layout.addWidget(self.name_input)

        note = QLabel("Выберите минимум двух участников")
        note.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 12px;")
        layout.addWidget(note)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 18px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 10px;
            }}
            QListWidget::item:selected {{ background-color: {self.colors['bg_tertiary']}; }}
            """
        )
        for user in self.users:
            item = QListWidgetItem(f"{user.get('name', 'Пользователь')}  @{user.get('username', '')}".strip())
            item.setData(Qt.ItemDataRole.UserRole, user.get("uid"))
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        cancel.setStyleSheet(self._secondary_button())
        buttons.addWidget(cancel)
        create = QPushButton("Создать")
        create.clicked.connect(self.submit)
        create.setStyleSheet(self._primary_button())
        buttons.addWidget(create)
        layout.addLayout(buttons)

    def submit(self):
        name = self.name_input.text().strip()
        selected = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        if not name:
            self.error_label.setText("Название обязательно")
            return
        if len(selected) < 2:
            self.error_label.setText("Нужно минимум два участника")
            return
        self.payload = {"name": name, "member_uids": selected}
        self.accept()

    def _input_style(self):
        return f"QLineEdit {{ background-color: {self.colors['bg_tertiary']}; color: {self.colors['text_primary']}; border: none; border-radius: 16px; padding: 12px 14px; }}"

    def _primary_button(self):
        return f"QPushButton {{ background-color: {self.colors['accent_primary']}; color: white; border: none; border-radius: 14px; padding: 10px 14px; font-weight: 600; }}"

    def _secondary_button(self):
        return f"QPushButton {{ background-color: transparent; color: {self.colors['text_secondary']}; border: none; border-radius: 14px; padding: 10px 14px; }}"
