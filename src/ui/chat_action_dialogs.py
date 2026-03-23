"""Dialogs used by chat actions."""
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)
from src.styles.themes import get_theme_colors

class ForwardMessagesDialog(QDialog):
    def __init__(self, users: list[dict], theme_name: str = "dark", parent=None):
        super().__init__(parent)
        self.users = users
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self.selected_uid = ""
        self.setModal(True)
        self.setWindowTitle("Переслать")
        self.resize(360, 420)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Переслать сообщения")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Выберите чат, куда отправить выделенные сообщения")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(subtitle)

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
                padding: 10px 12px;
                border-radius: 12px;
            }}
            QListWidget::item:selected {{
                background-color: {self.colors['bg_tertiary']};
            }}
            """
        )
        for user in self.users:
            item = QListWidgetItem(f"{user.get('name', 'Пользователь')} @{user.get('username', '')}".strip())
            item.setData(Qt.ItemDataRole.UserRole, user.get("uid"))
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(lambda _: self.accept_selection())
        layout.addWidget(self.list_widget, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        cancel.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {self.colors['text_secondary']}; border: none; padding: 10px 12px; }}"
        )
        buttons.addWidget(cancel)

        confirm = QPushButton("Переслать")
        confirm.clicked.connect(self.accept_selection)
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

    def accept_selection(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        self.selected_uid = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

class DeleteMessageDialog(QDialog):
    def __init__(self, allow_for_everyone: bool = True, theme_name: str = "dark", parent=None):
        """
        allow_for_everyone игнорируется, показываем обе кнопки всегда.
        Кнопка "Отмена" убрана.
        """
        super().__init__(parent)
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self.result_mode = ""
        self.setModal(True)
        self.setWindowTitle("Удалить сообщение")
        self.resize(320, 180)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Удалить сообщение?")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Выберите, где удалить сообщение")
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(subtitle)

        buttons = QHBoxLayout()
        
        # Кнопка "У меня"
        delete_me = QPushButton("У меня")
        delete_me.clicked.connect(lambda: self._finish("me"))
        delete_me.setStyleSheet(
            f"QPushButton {{ background-color: {self.colors['bg_tertiary']}; color: {self.colors['text_primary']}; border: none; border-radius: 14px; padding: 12px; }}"
        )
        buttons.addWidget(delete_me, 1)

        # Кнопка "У всех" (всегда видна)
        delete_all = QPushButton("У всех")
        delete_all.clicked.connect(lambda: self._finish("all"))
        # Красный цвет для акцента на деструктивном действии
        error_color = self.colors.get('error', '#EF5A5A')
        delete_all.setStyleSheet(
            f"QPushButton {{ background-color: {error_color}; color: white; border: none; border-radius: 14px; padding: 12px; font-weight: 600; }}"
        )
        buttons.addWidget(delete_all, 1)
        
        layout.addLayout(buttons)
        
        # ❌ КНОПКА "ОТМЕНА" УБРАНА ОТСЮДА

    def _finish(self, mode: str):
        self.result_mode = mode
        self.accept()

class EditMessageDialog(QDialog):
    def __init__(self, text: str, theme_name: str = "dark", parent=None):
        super().__init__(parent)
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self.result_text = ""
        self.setModal(True)
        self.setWindowTitle("Изменить сообщение")
        self.resize(380, 190)
        
        # Подключаем Enter к сохранению
        self.input_return_pressed = False
        
        self.build_ui(text)

    def build_ui(self, text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Изменить сообщение")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Введите новый текст")
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(subtitle)

        self.input = QLineEdit(text)
        self.input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 16px;
                padding: 12px 14px;
            }}
            """
        )
        # ✅ ГЛАВНОЕ ИЗМЕНЕНИЕ: Подключаем Enter к сохранению
        self.input.returnPressed.connect(self.accept_value)
        layout.addWidget(self.input)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        cancel.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {self.colors['text_secondary']}; border: none; padding: 10px 12px; }}"
        )
        buttons.addWidget(cancel)

        save = QPushButton("Сохранить")
        save.clicked.connect(self.accept_value)
        save.setStyleSheet(
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
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def accept_value(self):
        self.result_text = self.input.text().strip()
        if not self.result_text:
            return
        self.accept()