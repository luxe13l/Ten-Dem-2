"""Dialogs for creating contacts and groups."""
from __future__ import annotations
from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from src.styles import FONT_FAMILY
from src.styles.themes import get_theme_colors

class CreateContactDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить контакт")
        self.setModal(True)
        self.setFixedSize(400, 260)  # ✅ Чуть меньше высота
        self.payload = None
        
        self.colors = get_theme_colors("dark")
        if parent and hasattr(parent, 'current_user'):
            self.colors = get_theme_colors(getattr(parent.current_user, "theme", "dark"))
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Заголовок
        title = QLabel("Новый контакт")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']};")
        layout.addWidget(title)
        
        # Форма
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Имя
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Иван Иванов")
        self.name_input.setStyleSheet(self._input_style())
        form_layout.addRow("Имя:", self.name_input)
        
        # Телефон с маской
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("999 000-00-00")
        self.phone_input.setStyleSheet(self._input_style())
        self.phone_input.setMaxLength(18)  # ✅ ИСПРАВЛЕНО: 18 вместо 17
        self.phone_input.textChanged.connect(self.format_phone)
        
        form_layout.addRow("Телефон:", self.phone_input)
        
        # ✅ УДАЛЕНО: Текст-подсказка убран
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        
        buttons.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
            QPushButton[role='reject'] {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
            }}
            """
        )
        layout.addWidget(buttons)
        
    def _input_style(self):
        return f"""
        QLineEdit {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['divider']};
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            font-family: {FONT_FAMILY};
        }}
        QLineEdit:focus {{
            border-color: {self.colors['accent_primary']};
        }}
        """
    
    def format_phone(self, text):
        """Форматирует номер телефона как +7 (XXX) XXX-XX-XX"""
        digits = ''.join(filter(str.isdigit, text))
        
        if digits.startswith('7'):
            digits = digits[1:]
        elif digits.startswith('8'):
            digits = digits[1:]
        
        digits = digits[:10]  # ✅ Максимум 10 цифр
        
        formatted = "+7"
        if len(digits) > 0:
            formatted += f" ({digits[:3]}"
        if len(digits) > 3:
            formatted += f") {digits[3:6]}"
        if len(digits) > 6:
            formatted += f"-{digits[6:8]}"
        if len(digits) > 8:
            formatted += f"-{digits[8:10]}"
        
        self.phone_input.blockSignals(True)
        self.phone_input.setText(formatted)
        self.phone_input.blockSignals(False)
        self.phone_input.setCursorPosition(len(formatted))
    
    def on_accept(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        
        phone_digits = ''.join(filter(str.isdigit, phone))
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя контакта")
            return
        
        # ✅ ИСПРАВЛЕНО: Проверка на 10 цифр (без 7)
        if len(phone_digits) < 10:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер телефона")
            return
        
        self.payload = {
            "name": name,
            "phone": f"+{phone_digits}"
        }
        self.accept()


class CreateGroupDialog(QDialog):
    def __init__(self, users, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать группу")
        self.setModal(True)
        self.setFixedSize(450, 500)
        self.payload = None
        self.all_users = users
        self.selected_users = []
        
        self.colors = get_theme_colors("dark")
        if parent and hasattr(parent, 'current_user'):
            self.colors = get_theme_colors(getattr(parent.current_user, "theme", "dark"))
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Новая группа")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']};")
        layout.addWidget(title)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название группы")
        self.name_input.setStyleSheet(self._input_style())
        layout.addWidget(self.name_input)
        
        label = QLabel("Выберите участников:")
        label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        layout.addWidget(label)
        
        self.users_list = QListWidget()
        self.users_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
                border: 2px solid {self.colors['divider']};
                border-radius: 12px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 8px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
            }}
            """
        )
        self.users_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        for user in self.all_users:
            item = QListWidgetItem(f"{user.get('name', 'Unknown')} ({user.get('phone', '')})")
            item.setData(Qt.ItemDataRole.UserRole, user.get('uid'))
            self.users_list.addItem(item)
        
        layout.addWidget(self.users_list)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        
        buttons.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
            QPushButton[role='reject'] {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
            }}
            """
        )
        layout.addWidget(buttons)
        
    def _input_style(self):
        return f"""
        QLineEdit {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['divider']};
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            font-family: {FONT_FAMILY};
        }}
        QLineEdit:focus {{
            border-color: {self.colors['accent_primary']};
        }}
        """
    
    def on_accept(self):
        name = self.name_input.text().strip()
        selected_items = self.users_list.selectedItems()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название группы")
            return
        
        if len(selected_items) < 1:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одного участника")
            return
        
        selected_uids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        self.payload = {
            "name": name,
            "member_uids": selected_uids
        }
        self.accept()