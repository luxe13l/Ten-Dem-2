"""
Окно переписки с контактом
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QScrollArea, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.models.user import User
from src.models.message import Message
from src.database.messages_db import (send_message, get_messages, 
                                       listen_for_messages, mark_as_read)
from src.ui.message_bubble import MessageBubble
from src.ui.avatar_widget import AvatarWidget
from src.utils.settings import (
    COLOR_BACKGROUND, COLOR_PANEL, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_DIVIDER, COLOR_ACCENT, COLOR_ACCENT_HOVER, FONT_FAMILY, 
    FONT_SIZE_NAME, INPUT_BORDER_RADIUS, BUTTON_BORDER_RADIUS,
    COLOR_INPUT_BG, COLOR_INPUT_BORDER
)


class ChatWindow(QDialog):
    """Окно чата с контактом."""
    
    def __init__(self, current_user, contact, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.contact = contact
        self.message_listener = None
        self.typing_timer = QTimer()
        self.typing_timer.setInterval(2000)
        self.typing_timer.timeout.connect(self.stop_typing)
        self.init_ui()
        self.load_messages()
        self.listen_for_messages()
        
    def init_ui(self):
        """Инициализация интерфейса."""
        try:
            self.setWindowTitle(f"{self.contact.name}")
            self.setMinimumSize(700, 600)
            self.setModal(False)
            self.setStyleSheet(f"background-color: {COLOR_BACKGROUND};")
            
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Шапка
            header = QHBoxLayout()
            header.setContentsMargins(15, 12, 15, 12)
            header.setStyleSheet(f"background-color: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_DIVIDER};")
            
            back_btn = QPushButton("←")
            back_btn.setFixedSize(36, 36)
            back_btn.clicked.connect(self.close)
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_PRIMARY};
                    border: none;
                    border-radius: 18px;
                    font-size: 20px;
                    font-family: {FONT_FAMILY};
                }}
                QPushButton:hover {{ background-color: {COLOR_DIVIDER}; }}
            """)
            header.addWidget(back_btn)
            
            avatar = AvatarWidget(self.contact.name, self.contact.avatar_url, 40)
            header.addWidget(avatar)
            
            info = QVBoxLayout()
            info.setContentsMargins(10, 0, 0, 0)
            name_label = QLabel(self.contact.name)
            name_label.setFont(QFont(FONT_FAMILY, FONT_SIZE_NAME, QFont.Weight.Bold))
            name_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
            self.status_label = QLabel(self.contact.get_online_status())
            self.status_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px;")
            info.addWidget(name_label)
            info.addWidget(self.status_label)
            header.addLayout(info)
            header.addStretch()
            
            layout.addLayout(header)
            
            # Область сообщений
            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background-color: {COLOR_BACKGROUND};
                }}
            """)
            
            self.messages_container = QWidget()
            self.messages_layout = QVBoxLayout(self.messages_container)
            self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.messages_layout.setSpacing(5)
            self.messages_layout.setContentsMargins(15, 15, 15, 15)
            
            self.scroll.setWidget(self.messages_container)
            layout.addWidget(self.scroll, 1)
            
            # Панель ввода
            input_panel = QHBoxLayout()
            input_panel.setContentsMargins(15, 15, 15, 15)
            input_panel.setStyleSheet(f"background-color: {COLOR_PANEL};")
            
            attach_btn = QPushButton("📎")
            attach_btn.setFixedSize(40, 40)
            attach_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_SECONDARY};
                    border: none;
                    font-size: 18px;
                }}
                QPushButton:hover {{ color: {COLOR_TEXT_PRIMARY}; }}
            """)
            input_panel.addWidget(attach_btn)
            
            self.message_input = QTextEdit()
            self.message_input.setPlaceholderText("Сообщение...")
            self.message_input.setMaximumHeight(100)
            self.message_input.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLOR_INPUT_BG};
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_INPUT_BORDER};
                    border-radius: {INPUT_BORDER_RADIUS}px;
                    padding: 10px 16px;
                    font-size: 15px;
                    font-family: {FONT_FAMILY};
                }}
                QTextEdit:focus {{
                    border: 2px solid {COLOR_ACCENT};
                }}
            """)
            input_panel.addWidget(self.message_input, 1)
            
            send_btn = QPushButton("➤")
            send_btn.setFixedSize(40, 40)
            send_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: white;
                    border: none;
                    border-radius: {BUTTON_BORDER_RADIUS}px;
                    font-size: 18px;
                    font-weight: bold;
                    font-family: {FONT_FAMILY};
                }}
                QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
            """)
            send_btn.clicked.connect(self.send_message)
            input_panel.addWidget(send_btn)
            
            layout.addLayout(input_panel)
            
            self.setLayout(layout)
            
            self.message_input.installEventFilter(self)
            
        except Exception as e:
            print(f"Ошибка инициализации окна чата: {e}")
            import traceback
            traceback.print_exc()
    
    def eventFilter(self, obj, event):
        """Перехватывает нажатие Enter."""
        from PyQt6.QtCore import QEvent, Qt
        if obj == self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def load_messages(self):
        """Загружает историю переписки."""
        try:
            while self.messages_layout.count():
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            messages_data = get_messages(self.current_user.uid, self.contact.uid)
            
            for msg_data in messages_data:
                msg = Message.from_dict(msg_data, msg_data.get('id'))
                is_self = msg.from_uid == self.current_user.uid
                
                bubble = MessageBubble(msg, is_self)
                self.messages_layout.addWidget(bubble)
            
            self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            )
            
            self.mark_messages_read()
        except Exception as e:
            print(f"Ошибка загрузки сообщений: {e}")
    
    def send_message(self):
        """Отправляет новое сообщение."""
        try:
            text = self.message_input.toPlainText().strip()
            
            if not text:
                return
            
            msg_id = send_message(
                from_uid=self.current_user.uid,
                to_uid=self.contact.uid,
                text=text
            )
            
            if msg_id:
                from datetime import datetime
                msg = Message(
                    id=msg_id,
                    from_uid=self.current_user.uid,
                    to_uid=self.contact.uid,
                    text=text,
                    timestamp=datetime.now(),
                    delivered=True
                )
                
                bubble = MessageBubble(msg, is_self=True)
                self.messages_layout.addWidget(bubble)
                
                self.message_input.clear()
                
                self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                )
                
                self.stop_typing()
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
    
    def listen_for_messages(self):
        """Подписывается на новые сообщения."""
        try:
            def on_new_message(msg_data):
                if msg_data['from_uid'] == self.current_user.uid:
                    return
                
                msg = Message.from_dict(msg_data, msg_data.get('id'))
                bubble = MessageBubble(msg, is_self=False)
                
                self.messages_layout.addWidget(bubble)
                
                self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                )
                
                if msg.id:
                    mark_as_read(msg.id)
            
            self.message_listener = listen_for_messages(
                user_uid=self.current_user.uid,
                callback=on_new_message
            )
        except Exception as e:
            print(f"Ошибка подписки на сообщения: {e}")
    
    def mark_messages_read(self):
        """Отмечает сообщения как прочитанные."""
        pass
    
    def stop_typing(self):
        """Останавливает статус 'печатает'."""
        self.typing_timer.stop()
    
    def closeEvent(self, event):
        """Отписывается от слушателя при закрытии."""
        try:
            if self.message_listener and callable(self.message_listener):
                self.message_listener()
            self.stop_typing()
            event.accept()
        except Exception:
            event.accept()