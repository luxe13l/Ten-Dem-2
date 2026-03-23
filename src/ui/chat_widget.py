"""Working chat widget for Ten Dem."""
from __future__ import annotations
import os
from PyQt6.QtCore import QEvent, QMimeData, QSize, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QKeyEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QProgressDialog, QPushButton, QScrollArea, QStyle, QTextEdit, QVBoxLayout, QWidget
from src.database.messages_db import (
    QUICK_REACTIONS,
    delete_message as delete_message_record,
    edit_message as edit_message_record,
    forward_messages,
    get_messages,
    mark_chat_as_read,
    send_message as send_message_record,
    toggle_reaction,
)
from src.database.users_db import get_all_users
from src.models.message import Message, MessageStatus, MessageType
from src.styles import FONT_FAMILY
from src.styles.themes import get_theme_colors
from src.ui.attachment_preview_dialog import AttachmentPreviewDialog
from src.ui.auto_hide_scrollbar import AutoHideScrollBar
from src.ui.chat_action_dialogs import DeleteMessageDialog, EditMessageDialog, ForwardMessagesDialog
from src.ui.message_bubble import MessageBubble
from src.ui.photo_viewer_dialog import PhotoViewerDialog
from src.ui.settings_window import DEFAULT_SHORTCUTS

class ChatWidget(QWidget):
    chat_updated = pyqtSignal(str)
    
    def __init__(self, current_user, contact, shortcuts_map: dict | None = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.contact = contact
        self.shortcuts_map = {**DEFAULT_SHORTCUTS, **(shortcuts_map or {})}
        self.colors = get_theme_colors(getattr(self.current_user, "theme", "dark"))
        self.messages: list[Message] = []
        self.message_widgets: dict[str, MessageBubble] = {}
        self.replying_to: Message | None = None
        self.pinned_message_id = ""
        self.selection_mode = False
        self.selected_message_ids: set[str] = set()
        self._shortcuts: list[QShortcut] = []
        self.setAcceptDrops(True)
        self.build_ui()
        self._bind_shortcuts()
        self.load_messages(animated=False)

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._create_header())
        root.addWidget(self._create_selection_bar())

        self.pinned_bar = QFrame()
        self.pinned_bar.hide()
        self.pinned_bar.setStyleSheet(
            f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-bottom: 1px solid {self.colors['divider']}; }}"
        )
        pinned_layout = QHBoxLayout(self.pinned_bar)
        pinned_layout.setContentsMargins(16, 8, 16, 8)
        self.pinned_label = QLabel()
        self.pinned_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 13px; background: transparent;")
        pinned_layout.addWidget(self.pinned_label, 1)
        pin_clear = QPushButton("Снять")
        pin_clear.setStyleSheet(self._ghost_button_style())
        pin_clear.clicked.connect(self.clear_pinned_message)
        pinned_layout.addWidget(pin_clear)
        root.addWidget(self.pinned_bar)

        self.reply_bar = QFrame()
        self.reply_bar.hide()
        self.reply_bar.setStyleSheet(
            f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-bottom: 1px solid {self.colors['divider']}; }}"
        )
        reply_layout = QHBoxLayout(self.reply_bar)
        reply_layout.setContentsMargins(16, 8, 16, 8)
        self.reply_label = QLabel()
        self.reply_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 13px; background: transparent;")
        reply_layout.addWidget(self.reply_label, 1)
        reply_clear = QPushButton("Отмена")
        reply_clear.setStyleSheet(self._ghost_button_style())
        reply_clear.clicked.connect(self.clear_reply)
        reply_layout.addWidget(reply_clear)
        root.addWidget(self.reply_bar)

        self.messages_scroll = QScrollArea()
        self.messages_scroll.setVerticalScrollBar(AutoHideScrollBar(parent=self.messages_scroll))
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setStyleSheet(
            f"""
            QScrollArea {{ border: none; background: {self.colors['bg_secondary']}; border-radius: 28px; }}
            QScrollBar:vertical {{ width: 10px; background: transparent; margin: 8px 6px 8px 0; }}
            QScrollBar::handle:vertical {{ background: {'rgba(25,25,28,0.16)' if self.current_user.theme == 'light' else 'rgba(255,255,255,0.18)'}; border-radius: 999px; min-height: 42px; }}
            QScrollBar::handle:vertical:hover {{ background: {'rgba(25,25,28,0.24)' if self.current_user.theme == 'light' else 'rgba(255,255,255,0.22)'}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; border: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
            """
        )

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(18, 18, 18, 18)
        self.messages_layout.setSpacing(10)

        self.empty_state = QLabel("Здесь пока пусто. Напишите первое сообщение.")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 14px; padding: 60px 0 20px 0; background: transparent;"
        )
        self.messages_layout.addWidget(self.empty_state)
        self.messages_layout.addStretch()
        self.messages_scroll.setWidget(self.messages_container)
        root.addWidget(self.messages_scroll, 1)
        root.addWidget(self._create_input_panel())

    def _std_icon(self, name: str):
        pixmap = getattr(QStyle.StandardPixmap, name, None)
        if pixmap is None:
            return QIcon()
        return self.style().standardIcon(pixmap)

    def _create_header(self):
        frame = QFrame()
        frame.setFixedHeight(78)
        header_bg = "rgba(255, 255, 255, 0.86)" if self.current_user.theme == "light" else "rgba(22, 22, 22, 0.92)"
        frame.setStyleSheet(
            f"QFrame {{ background-color: {header_bg}; border: none; border-radius: 28px 28px 0 0; border-bottom: 1px solid {self.colors['divider']}; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 0, 20, 0)

        avatar = QLabel((self.contact.name or "?")[0].upper())
        avatar.setFixedSize(42, 42)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"""
            QLabel {{
                background-color: {self.colors['accent_primary']};
                color: white;
                border-radius: 21px;
                font-size: 17px;
                font-weight: 600;
            }}
            """
        )
        layout.addWidget(avatar)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel(self.contact.name or "Пользователь")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 16px; font-weight: 600; background: transparent;")
        title_layout.addWidget(title)
        status_text = "в сети" if self.contact.status == "online" else "был недавно"
        status = QLabel(status_text)
        status.setStyleSheet(f"color: {self.colors['online']}; font-size: 12px; background: transparent;")
        title_layout.addWidget(status)
        layout.addLayout(title_layout)
        layout.addStretch()

        menu_button = QPushButton("⋮")
        menu_button.setFixedSize(40, 40)
        menu_button.setStyleSheet(self._icon_button_style())
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        select_action = menu.addAction("Выбрать сообщения")
        select_action.triggered.connect(self.enter_selection_mode)
        clear_action = menu.addAction("Очистить историю")
        clear_action.triggered.connect(self.clear_history)
        select_action.setIcon(self._std_icon("SP_DialogApplyButton"))
        clear_action.setIcon(self._std_icon("SP_TrashIcon"))
        menu_button.setMenu(menu)
        layout.addWidget(menu_button)
        return frame

    def _create_selection_bar(self):
        """Панель действий при выборе сообщений (Переслать / Удалить)"""
        self.selection_bar = QFrame()
        self.selection_bar.hide()
        self.selection_bar.setStyleSheet(
            f"QFrame {{ background-color: {self.colors['bg_secondary']}; border-bottom: 1px solid {self.colors['divider']}; }}"
        )
        layout = QHBoxLayout(self.selection_bar)
        layout.setContentsMargins(16, 10, 16, 10)
        
        self.selection_label = QLabel("Выбрано: 0")
        self.selection_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self.selection_label)
        layout.addStretch()

        # Кнопка ПЕРЕСЛАТЬ
        forward_btn = QPushButton("Переслать")
        forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forward_btn.setStyleSheet(self._ghost_button_style(primary=True))
        forward_btn.clicked.connect(self.forward_selected_messages)
        layout.addWidget(forward_btn)

        # Кнопка УДАЛИТЬ
        delete_btn = QPushButton("Удалить")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(self._ghost_button_style(primary=False))
        delete_btn.clicked.connect(self.delete_selected_messages)
        layout.addWidget(delete_btn)

        # ❌ КНОПКУ "НАЗАД" УБРАЛИ — она не нужна
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._ghost_button_style())
        cancel_btn.clicked.connect(self.exit_selection_mode)
        layout.addWidget(cancel_btn)
        return self.selection_bar

    def _create_input_panel(self):
        panel = QFrame()
        panel.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.colors['bg_secondary']};
                border-top: 1px solid {self.colors['divider']};
                border-radius: 0 0 28px 28px;
            }}
            """
        )
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons")

        self.attach_btn = QPushButton()
        self.attach_btn.setFixedSize(42, 42)
        self.attach_btn.setIcon(QIcon(os.path.join(assets_root, "attach.svg")))
        self.attach_btn.setIconSize(QSize(18, 18))
        self.attach_btn.setStyleSheet(self._icon_button_style())
        self.attach_btn.clicked.connect(self.on_attach_clicked)
        layout.addWidget(self.attach_btn)

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(58)
        self.input_field.setPlaceholderText("Написать сообщение")
        self.input_field.installEventFilter(self)
        self.input_field.textChanged.connect(self.on_text_changed)
        self.input_field.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 24px;
                padding: 10px 16px;
                font-size: 14px;
                font-family: {FONT_FAMILY};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 8px 6px 8px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {'rgba(25,25,28,0.16)' if self.current_user.theme == 'light' else 'rgba(255,255,255,0.18)'};
                min-height: 28px;
                border-radius: 999px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {'rgba(25,25,28,0.24)' if self.current_user.theme == 'light' else 'rgba(255,255,255,0.22)'};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                width: 0px;
                border: none;
                background: transparent;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar::up-arrow, QScrollBar::down-arrow {{
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }}
            """
        )
        self.input_field.setMinimumHeight(44)
        layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton()
        self.send_btn.setEnabled(False)
        self.send_btn.setFixedSize(42, 42)
        self.send_btn.setIcon(QIcon(os.path.join(assets_root, "send.svg")))
        self.send_btn.setIconSize(QSize(18, 18))
        self.send_btn.clicked.connect(self.on_send_clicked)
        self.send_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {self.colors['accent_primary']};
                border: none;
                border-radius: 999px;
            }}
            QPushButton:hover {{ background-color: rgba(68, 148, 74, 0.08); }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {self.colors['text_tertiary']};
            }}
            """
        )
        layout.addWidget(self.send_btn)
        return panel

    def _bind_shortcuts(self):
        for shortcut in self._shortcuts:
            shortcut.deleteLater()
        self._shortcuts = []
        bindings = {
            "send": self._send_shortcut_triggered,
            "escape": self._escape_shortcut_triggered,
        }
        for key, handler in bindings.items():
            sequence = self.shortcuts_map.get(key)
            if not sequence:
                continue
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _send_shortcut_triggered(self):
        if self.input_field.hasFocus() and self.send_btn.isEnabled():
            self.on_send_clicked()

    def _escape_shortcut_triggered(self):
        if self.selection_mode:
            self.exit_selection_mode()
        elif self.reply_bar.isVisible():
            self.clear_reply()

    def load_messages(self, animated: bool = True):
        self._show_loading_state()
        QTimer.singleShot(80 if animated else 0, self._finish_loading_messages)

    def _show_loading_state(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                if widget is self.empty_state:
                    widget.hide()
                else:
                    widget.deleteLater()
        for _ in range(3):
            skeleton = QFrame()
            skeleton.setFixedHeight(54)
            skeleton.setStyleSheet(f"QFrame {{ background-color: {self.colors['bg_tertiary']}; border-radius: 18px; }}")
            self.messages_layout.addWidget(skeleton)
        self.messages_layout.addStretch()

    def _finish_loading_messages(self):
        self.messages.clear()
        self.message_widgets.clear()
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                if widget is self.empty_state:
                    widget.hide()
                else:
                    widget.deleteLater()

        records = get_messages(self.current_user.uid, self.contact.uid, limit=200)
        records = [record for record in records if self.current_user.uid not in record.get("deleted_for", [])]
        self.messages_layout.addWidget(self.empty_state)
        self.empty_state.setVisible(not records)

        for record in records:
            message = Message.from_dict(record, record.get("id"))
            self._add_message_widget(message)
        self.messages_layout.addStretch()
        mark_chat_as_read(self.current_user.uid, self.contact.uid)
        QTimer.singleShot(0, self.scroll_to_bottom)

    def _add_message_widget(self, message: Message):
        message.selection_enabled = self.selection_mode
        message.is_selected = message.id in self.selected_message_ids
        bubble = MessageBubble(
            message,
            message.from_uid == self.current_user.uid,
            current_user_uid=self.current_user.uid,
            theme_name=getattr(self.current_user, "theme", "dark"),
            parent=self.messages_container,
        )
        bubble.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        bubble.customContextMenuRequested.connect(lambda pos, msg_id=message.id, widget=bubble: self.show_message_menu(widget, pos, msg_id))
        bubble.context_menu_requested.connect(lambda pos, msg_id=message.id, widget=bubble: self.show_message_menu(widget, pos, msg_id))
        bubble.clicked.connect(self.on_bubble_clicked)
        bubble.photo_requested.connect(self.open_photo_viewer)
        bubble.reaction_clicked.connect(self.apply_reaction)
        self.messages_layout.insertWidget(max(0, self.messages_layout.count() - 1), bubble)
        self.messages.append(message)
        self.message_widgets[message.id] = bubble
        self.empty_state.hide()

    def on_bubble_clicked(self, message_id: str):
        if not self.selection_mode:
            return
        if message_id in self.selected_message_ids:
            self.selected_message_ids.remove(message_id)
        else:
            self.selected_message_ids.add(message_id)
        self._refresh_selection_widgets()

    def show_message_menu(self, bubble: MessageBubble, pos, message_id: str):
        message = self._find_message(message_id)
        if not message:
            return

        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        reply_action = menu.addAction("Ответить")
        pin_action = menu.addAction("Закрепить")
        react_menu = menu.addMenu("Реакции")
        react_menu.setStyleSheet(self._menu_style())
        reply_action.setIcon(self._std_icon("SP_ArrowBack"))
        pin_action.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "attach.svg")))
        react_menu.setIcon(self._std_icon("SP_DialogApplyButton"))
        for emoji in QUICK_REACTIONS:
            action = react_menu.addAction(emoji)
            action.triggered.connect(lambda _, value=emoji, msg_id=message.id: self.apply_reaction(msg_id, value))
        menu.addSeparator()
        select_action = menu.addAction("Выбрать")
        forward_action = menu.addAction("Переслать")
        edit_action = menu.addAction("Изменить") if message.from_uid == self.current_user.uid else None
        delete_action = menu.addAction("Удалить")
        select_action.setIcon(self._std_icon("SP_DialogApplyButton"))
        forward_action.setIcon(self._std_icon("SP_ArrowForward"))
        if edit_action:
            edit_action.setIcon(self._std_icon("SP_FileDialogContentsView"))
        delete_action.setIcon(self._std_icon("SP_TrashIcon"))

        action = menu.exec(bubble.mapToGlobal(pos))
        if action == reply_action:
            self.reply_to_message(message)
        elif action == pin_action:
            self.pin_message(message)
        elif action == select_action:
            self.enter_selection_mode()
            self.selected_message_ids.add(message.id)
            self._refresh_selection_widgets()
        elif action == forward_action:
            self.enter_selection_mode()
            self.selected_message_ids = {message.id}
            self._refresh_selection_widgets()
            self.forward_selected_messages()
        elif edit_action and action == edit_action:
            self.edit_message(message)
        elif action == delete_action:
            # Для одиночного удаления через меню
            self.selected_message_ids = {message.id}
            self.delete_selected_messages()

    def on_send_clicked(self):
        text = self.input_field.toPlainText().strip()
        if text:
            self._send(text=text, message_type=MessageType.TEXT)

    def _send(self, text: str, message_type: MessageType, file_url: str = "", file_name: str = "", file_size: int = 0, poll_options: list[str] | None = None):
        message_id = send_message_record(
            from_uid=self.current_user.uid,
            to_uid=self.contact.uid,
            text=text,
            message_type=message_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            reply_to_id=self.replying_to.id if self.replying_to else "",
            poll_options=poll_options or [],
        )
        if not message_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось отправить сообщение.")
            return

        message = Message(
            id=message_id,
            from_uid=self.current_user.uid,
            to_uid=self.contact.uid,
            text=text,
            message_type=message_type,
            status=MessageStatus.SENT,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            reply_to_id=self.replying_to.id if self.replying_to else "",
            poll_options=poll_options or [],
        )
        self._add_message_widget(message)
        self.input_field.clear()
        self.clear_reply()
        QTimer.singleShot(50, self.scroll_to_bottom)
        self.chat_updated.emit(self.contact.uid)

    def reply_to_message(self, message: Message):
        self.replying_to = message
        preview = message.text or message.file_name or "медиа"
        self.reply_label.setText(f"Ответ на: {preview[:60]}")
        self.reply_bar.show()
        self.input_field.setFocus()

    def clear_reply(self):
        self.replying_to = None
        self.reply_bar.hide()
        self.reply_label.clear()

    def pin_message(self, message: Message):
        preview = message.text or message.file_name or "медиа"
        self.pinned_message_id = message.id
        self.pinned_label.setText(f"Закреплено: {preview[:70]}")
        self.pinned_bar.show()

    def clear_pinned_message(self):
        self.pinned_message_id = ""
        self.pinned_bar.hide()
        self.pinned_label.clear()

    def edit_message(self, message: Message):
        dialog = EditMessageDialog(message.text, getattr(self.current_user, "theme", "dark"), self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        new_text = dialog.result_text.strip()
        if not new_text:
            return
        if not edit_message_record(message.id, new_text):
            QMessageBox.warning(self, "Ошибка", "Не удалось изменить сообщение.")
            return
        message.text = new_text
        message.is_edited = True
        bubble = self.message_widgets.get(message.id)
        if bubble:
            bubble.update_message(message)
        self.chat_updated.emit(self.contact.uid)

    def request_delete_message(self, message: Message):
        # ✅ ВСЕГДА ПОКАЗЫВАЕМ ДИАЛОГ С ВЫБОРОМ "У МЕНЯ" / "У ВСЕХ"
        dialog = DeleteMessageDialog(
            allow_for_everyone=True, 
            theme_name=getattr(self.current_user, "theme", "dark"),
            parent=self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        self.delete_message(message, for_everyone=dialog.result_mode == "all")

    def delete_message(self, message: Message, for_everyone: bool):
        if not delete_message_record(message.id, for_everyone=for_everyone, deleted_by=self.current_user.uid):
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить сообщение.")
            return
        bubble = self.message_widgets.pop(message.id, None)
        if bubble:
            bubble.deleteLater()
        self.messages = [item for item in self.messages if item.id != message.id]
        self.selected_message_ids.discard(message.id)
        self.empty_state.setVisible(not self.messages)
        self._refresh_selection_widgets()
        self.chat_updated.emit(self.contact.uid)

    # ============================================================
    # МАССОВОЕ УДАЛЕНИЕ ВЫДЕЛЕННЫХ СООБЩЕНИЙ
    # ============================================================
    def delete_selected_messages(self):
        if not self.selected_message_ids:
            QMessageBox.information(self, "Удаление", "Сначала выберите сообщения.")
            return

        # ✅ МЫ ВСЕГДА ПОКАЗЫВАЕМ ВЫБОР "У МЕНЯ" / "У ВСЕХ"
        # Не важно, свои сообщения или чужие. Пользователь сам решает.
        
        dialog = DeleteMessageDialog(
            allow_for_everyone=True,  # Всегда разрешаем выбор
            theme_name=getattr(self.current_user, "theme", "dark"),
            parent=self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        
        for_everyone = (dialog.result_mode == "all")
        
        # Удаляем циклом
        ids_to_remove = list(self.selected_message_ids)
        for msg_id in ids_to_remove:
            message = self._find_message(msg_id)
            if message:
                # Вызываем функцию удаления из БД
                # База данных сама решит, что можно удалить физически, а что пометить
                delete_message_record(message.id, for_everyone=for_everyone, deleted_by=self.current_user.uid)
                
                # Удаляем из UI
                bubble = self.message_widgets.pop(message.id, None)
                if bubble:
                    bubble.deleteLater()
                self.messages = [m for m in self.messages if m.id != message.id]
        
        # Очищаем выделение
        self.selected_message_ids.clear()
        self.exit_selection_mode()
        self.empty_state.setVisible(not self.messages)
        self.chat_updated.emit(self.contact.uid)
    # ============================================================

    def apply_reaction(self, message_id: str, emoji: str):
        reactions = toggle_reaction(message_id, emoji, self.current_user.uid)
        if reactions is None:
            return
        message = self._find_message(message_id)
        if not message:
            return
        message.reactions = reactions
        bubble = self.message_widgets.get(message.id)
        if bubble:
            bubble.update_message(message)

    def clear_history(self):
        if QMessageBox.question(self, "Очистить историю", "Удалить переписку только у вас?") != QMessageBox.StandardButton.Yes:
            return
        for message in list(self.messages):
            self.delete_message(message, for_everyone=False)

    def enter_selection_mode(self):
        if self.selection_mode:
            return
        self.selection_mode = True
        self.selection_bar.show()
        self._refresh_selection_widgets()

    def exit_selection_mode(self):
        self.selection_mode = False
        self.selected_message_ids.clear()
        self.selection_bar.hide()
        self._refresh_selection_widgets()

    def _refresh_selection_widgets(self):
        self.selection_label.setText(f"Выбрано: {len(self.selected_message_ids)}")
        for message in self.messages:
            bubble = self.message_widgets.get(message.id)
            if bubble:
                bubble.set_selection_state(self.selection_mode, message.id in self.selected_message_ids)
        if self.selection_mode and not self.selected_message_ids:
            self.selection_label.setText("Выберите сообщения")

    def forward_selected_messages(self):
        if not self.selected_message_ids:
            QMessageBox.information(self, "Пересылка", "Сначала выберите сообщения.")
            return
        users = [user for user in get_all_users() if user.get("uid") not in {self.current_user.uid, self.contact.uid}]
        if not users:
            QMessageBox.information(self, "Пересылка", "Пока нет других чатов для пересылки.")
            return
        dialog = ForwardMessagesDialog(users, getattr(self.current_user, "theme", "dark"), self)
        if dialog.exec() != dialog.DialogCode.Accepted or not dialog.selected_uid:
            return
        created = forward_messages(self.current_user.uid, list(self.selected_message_ids), dialog.selected_uid)
        if not created:
            QMessageBox.warning(self, "Пересылка", "Не удалось переслать сообщения.")
            return
        self.exit_selection_mode()
        QMessageBox.information(self, "Пересылка", f"Переслано сообщений: {len(created)}")

    def on_text_changed(self):
        self.send_btn.setEnabled(bool(self.input_field.toPlainText().strip()))

    def on_attach_clicked(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        photo_action = menu.addAction("Фото")
        video_action = menu.addAction("Видео")
        poll_action = menu.addAction("Опрос")
        file_action = menu.addAction("Файл")
        photo_action.setIcon(self._std_icon("SP_FileIcon"))
        video_action.setIcon(self._std_icon("SP_MediaPlay"))
        poll_action.setIcon(self._std_icon("SP_DialogApplyButton"))
        file_action.setIcon(self._std_icon("SP_FileLinkIcon"))
        action = menu.exec(self.attach_btn.mapToGlobal(self.attach_btn.rect().bottomLeft()))
        if action == photo_action:
            self.attach_photo()
        elif action == video_action:
            self.attach_video()
        elif action == poll_action:
            self.attach_poll()
        elif action == file_action:
            self.attach_file()

    def attach_photo(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)")
        if files:
            self.preview_and_send_files(files, MessageType.PHOTO)

    def attach_video(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите видео", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if files:
            self.preview_and_send_files(files, MessageType.VIDEO)

    def attach_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы", "", "All Files (*)")
        if files:
            self.preview_and_send_files(files, MessageType.FILE)

    def attach_poll(self):
        QMessageBox.information(self, "Опрос", "Нормальный экран опросов сделаю отдельным блоком, чтобы не оставлять сырые системные окна.")

    def preview_and_send_files(self, files: list[str], kind: MessageType):
        dialog = AttachmentPreviewDialog(files, parent=self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        progress = QProgressDialog("Подготовка файлов...", "Отмена", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        for index, file_path in enumerate(files, start=1):
            if progress.wasCanceled():
                break
            progress.setValue(index - 1)
            progress.setLabelText(f"Отправка: {os.path.basename(file_path)}")
            self._send(
                text=os.path.basename(file_path) if kind == MessageType.FILE else "",
                message_type=kind,
                file_url=file_path,
                file_name=os.path.basename(file_path),
                file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            )
        progress.setValue(len(files))

    def open_photo_viewer(self, message_id: str):
        media = [message.to_dict() for message in self.messages if message.message_type in {MessageType.PHOTO, MessageType.VIDEO}]
        if not media:
            return
        target_index = next((index for index, item in enumerate(media) if item.get("id") == message_id), 0)
        viewer = PhotoViewerDialog(media, target_index, getattr(self.current_user, "theme", "dark"), self)
        viewer.exec()

    def _find_message(self, message_id: str) -> Message | None:
        for message in self.messages:
            if message.id == message_id:
                return message
        return None

    def scroll_to_bottom(self):
        bar = self.messages_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
                if self.send_btn.isEnabled():
                    self.on_send_clicked()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape and self.selection_mode:
            self.exit_selection_mode()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._mime_has_files(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        files = self._extract_files(event.mimeData())
        if not files:
            return
        self.preview_and_send_files(files, self._guess_kind(files))
        event.acceptProposedAction()

    def _mime_has_files(self, mime: QMimeData) -> bool:
        return mime.hasUrls() and any(url.isLocalFile() for url in mime.urls())

    def _extract_files(self, mime: QMimeData) -> list[str]:
        return [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]

    def _guess_kind(self, files: list[str]) -> MessageType:
        if all(file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) for file in files):
            return MessageType.PHOTO
        if all(file.lower().endswith((".mp4", ".mov", ".avi", ".mkv")) for file in files):
            return MessageType.VIDEO
        return MessageType.FILE

    def _menu_style(self):
        return f"""
        QMenu {{
            background-color: {self.colors['bg_secondary']};
            color: {self.colors['text_primary']};
            border: none;
            border-radius: 18px;
            padding: 8px;
        }}
        QMenu::item {{
            padding: 10px 16px;
            border-radius: 14px;
        }}
        QMenu::item:selected {{
            background-color: {self.colors['bg_tertiary']};
        }}
        """

    def _icon_button_style(self):
        return f"""
        QPushButton {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['icon_default']};
            border: none;
            border-radius: 999px;
        }}
        QPushButton:hover {{
            background-color: #272727;
            color: {self.colors['text_primary']};
        }}
        """

    def _ghost_button_style(self, primary: bool = False):
        color = self.colors["accent_primary"] if primary else self.colors["text_secondary"]
        hover = self.colors["text_primary"] if not primary else self.colors["accent_hover"]
        return f"""
        QPushButton {{
            background-color: transparent;
            color: {color};
            border: none;
            padding: 4px 8px;
            font-weight: {'600' if primary else '400'};
        }}
        QPushButton:hover {{
            color: {hover};
        }}
        """