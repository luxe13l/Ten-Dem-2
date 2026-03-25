"""Main messenger window with Navigation Rail."""
from __future__ import annotations
import uuid
import os
from PyQt6.QtCore import QSize, Qt, QTimer, QRegularExpression
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
    QDialog,
)
from src.database.local_store import load_store, save_store
from src.database.messages_db import get_chat_summaries
from src.database.users_db import create_user, get_all_users, set_online_status, find_user_by_phone, add_contact_to_list, get_contacts, update_user, get_db
from src.models.user import User
from src.styles import FONT_FAMILY, LEFT_PANEL_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from src.styles.themes import get_theme_colors, apply_theme
from src.ui.auto_hide_scrollbar import AutoHideScrollBar
from src.ui.chat_creation_dialogs import CreateContactDialog, CreateGroupDialog
from src.ui.chat_widget import ChatWidget
from src.ui.contact_info_dialog import ContactInfoDialog
from src.ui.contact_item import ContactItem
from src.ui.settings_window import DEFAULT_SHORTCUTS, SettingsWindow

class MainWindow(QMainWindow):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.colors = get_theme_colors(getattr(self.current_user, "theme", "dark"))
        self.current_chat_widget = None
        self.settings_window = None
        self.contact_widgets = {}
        self.contact_list_widgets = {}
        self.shortcuts_map = self._load_shortcuts()
        self._shortcuts: list[QShortcut] = []
        self.current_view = "chats"
        
        self.icons_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "icons"
        )
        
        self.init_ui()
        self._bind_shortcuts()
        set_online_status(self.current_user.uid, "online")

    def _load_shortcuts(self):
        settings = load_store().get("settings", {}).get(self.current_user.uid, {})
        return {**DEFAULT_SHORTCUTS, **settings.get("shortcuts", {})}

    def init_ui(self):
        self.setWindowTitle(f"Ten Dem | {self.current_user.name}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1280, 820)
        self.setStyleSheet(f"QMainWindow {{ background-color: {self.colors['bg_primary']}; }}")

        central = QWidget()
        central.setObjectName("mainSurface")
        central.setStyleSheet(f"#mainSurface {{ background-color: {self.colors['bg_primary']}; }}")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        
        shell = self._create_nav_shell()
        layout.addWidget(shell)
        
        self.right_panel = self._create_right_panel()
        layout.addWidget(self.right_panel, 1)

    def _create_nav_shell(self):
        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(14)
        
        rail = self._create_nav_rail()
        shell_layout.addWidget(rail)
        
        content_panel = self._create_content_panel()
        shell_layout.addWidget(content_panel)
        
        return shell

    def _create_nav_rail(self):
        rail = QWidget()
        rail.setFixedWidth(74)
        rail.setObjectName("navRail")
        rail.setStyleSheet(
            f"""
            QWidget#navRail {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 28px;
                border: 1px solid {self.colors['divider']};
            }}
            """
        )
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(0, 18, 0, 18)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.nav_btn_chats = self._rail_icon_button("chat.svg", active=True)
        self.nav_btn_chats.setToolTip("Чаты")
        self.nav_btn_chats.clicked.connect(lambda: self.switch_view("chats"))
        
        self.nav_btn_contacts = self._rail_icon_button("contact.svg", active=False)
        self.nav_btn_contacts.setToolTip("Контакты")
        self.nav_btn_contacts.clicked.connect(lambda: self.switch_view("contacts"))
        
        layout.addWidget(self.nav_btn_chats, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.nav_btn_contacts, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addStretch()
        
        settings_btn = self._rail_icon_button("settings.svg")
        settings_btn.setToolTip("Настройки")
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        
        return rail

    def _rail_icon_button(self, icon_name: str, active: bool = False):
        button = QPushButton()
        button.setFixedSize(44, 44)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        icon_path = os.path.join(self.icons_path, icon_name)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(20, 20))
        
        bg_color = "rgba(68, 148, 74, 0.15)" if active else "transparent"
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg_color};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['bg_tertiary']};
            }}
            """
        )
        button.active_style = f"background-color: rgba(68, 148, 74, 0.15); border: none; border-radius: 18px;"
        button.inactive_style = f"background-color: transparent; border: none; border-radius: 18px;"
        return button

    def _update_nav_buttons(self, view_name: str):
        for btn in [self.nav_btn_chats, self.nav_btn_contacts]:
            btn.setStyleSheet(btn.inactive_style)
        
        if view_name == "chats":
            self.nav_btn_chats.setStyleSheet(self.nav_btn_chats.active_style)
        elif view_name == "contacts":
            self.nav_btn_contacts.setStyleSheet(self.nav_btn_contacts.active_style)

    def _create_content_panel(self):
        panel = QWidget()
        panel.setFixedWidth(LEFT_PANEL_WIDTH)
        panel.setObjectName("sidebarPanel")
        panel.setStyleSheet(
            f"""
            QWidget#sidebarPanel {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 28px;
                border: 1px solid {self.colors['divider']};
            }}
            """
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 24, 24, 10)
        self.view_title = QLabel("Чаты")
        self.view_title.setFont(QFont(FONT_FAMILY, 22, QFont.Weight.Bold))
        self.view_title.setStyleSheet(f"color: {self.colors['text_primary']};")
        header.addWidget(self.view_title)
        header.addStretch()
        layout.addLayout(header)

        subtitle = QLabel((getattr(self.current_user, "username", "") or self.current_user.name or "ten dem").lower())
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px; padding: 0 24px 10px 24px;")
        layout.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск")
        self.search_input.textChanged.connect(self.filter_current_view)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                margin: 0 16px 18px 16px;
                padding: 13px 18px;
                border: none;
                border-radius: 26px;
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
                font-size: 14px;
            }}
            """
        )
        layout.addWidget(self.search_input)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")

        self.chats_list_widget = QListWidget()
        self.chats_list_widget.setVerticalScrollBar(AutoHideScrollBar(parent=self.chats_list_widget))
        self.chats_list_widget.itemClicked.connect(self.open_chat_from_item)
        self.chats_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chats_list_widget.customContextMenuRequested.connect(self.open_chat_context_menu)
        self.chats_list_widget.setStyleSheet(self._list_style())
        self.stacked_widget.addWidget(self.chats_list_widget)

        self.contacts_list_widget = QListWidget()
        self.contacts_list_widget.setVerticalScrollBar(AutoHideScrollBar(parent=self.contacts_list_widget))
        self.contacts_list_widget.itemClicked.connect(self.open_chat_from_contact)
        self.contacts_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contacts_list_widget.customContextMenuRequested.connect(self.open_contact_context_menu)
        self.contacts_list_widget.setStyleSheet(self._list_style())
        self.stacked_widget.addWidget(self.contacts_list_widget)

        layout.addWidget(self.stacked_widget, 1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(18, 0, 18, 26)
        bottom.addStretch()

        self.new_item_button = QPushButton()
        self.new_item_button.setFixedSize(48, 48)
        self.new_item_button.setIcon(QIcon(os.path.join(self.icons_path, "plus.svg")))
        self.new_item_button.setIconSize(QSize(18, 18))
        self.new_item_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_item_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
                border: none;
                border-radius: 24px;
            }}
            QPushButton:hover {{ background-color: {self.colors['accent_hover']}; }}
            """
        )
        shadow = QGraphicsDropShadowEffect(self.new_item_button)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(self._shadow_color())
        self.new_item_button.setGraphicsEffect(shadow)
        
        self.new_item_button.clicked.connect(self.on_add_button_clicked)
        
        bottom.addWidget(self.new_item_button, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(bottom)

        return panel

    def _list_style(self):
        return f"""
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 0 8px 0 8px;
        }}
        QListWidget::item {{
            margin: 0 0 8px 0;
            border-radius: 20px;
            background: transparent;
        }}
        QListWidget::item:selected {{ background-color: transparent; }}
        QListWidget::item:hover {{ background-color: transparent; }}
        QScrollBar:vertical {{ width: 10px; background: transparent; margin: 10px 6px 76px 0; }}
        QScrollBar::handle:vertical {{ background: rgba(255,255,255,0.18); border-radius: 999px; min-height: 42px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; border: none; }}
        """

    def _create_right_panel(self):
        panel = QWidget()
        panel.setObjectName("chatPanel")
        panel.setStyleSheet(
            f"""
            QWidget#chatPanel {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 30px;
                border: 1px solid {self.colors['divider']};
            }}
            """
        )
        right_layout = QVBoxLayout(panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.placeholder = QLabel("Выберите чат, чтобы начать общение")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 18px;")
        right_layout.addWidget(self.placeholder)
        
        return panel

    def switch_view(self, view_name: str):
        self.current_view = view_name
        self._update_nav_buttons(view_name)
        
        if view_name == "chats":
            self.view_title.setText("Чаты")
            self.stacked_widget.setCurrentIndex(0)
            self.new_item_button.setToolTip("Создать чат или группу")
            self.load_chats()
        elif view_name == "contacts":
            self.view_title.setText("Контакты")
            self.stacked_widget.setCurrentIndex(1)
            self.new_item_button.setToolTip("Добавить контакт")
            self.load_contacts_list()

    def on_add_button_clicked(self):
        if self.current_view == "chats":
            self.open_create_menu()
        elif self.current_view == "contacts":
            self.create_contact_flow()

    def open_create_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        contact_action = menu.addAction("Создать контакт")
        group_action = menu.addAction("Создать группу")
        contact_action.setIcon(self._std_icon("SP_FileIcon"))
        group_action.setIcon(self._std_icon("SP_FileDialogNewFolder"))
        anchor = self.new_item_button.mapToGlobal(self.new_item_button.rect().topLeft())
        action = menu.exec(anchor)
        if action == contact_action:
            self.create_contact_flow()
        elif action == group_action:
            self.create_group()

    def create_contact_flow(self):
        dialog = CreateContactDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted or not dialog.payload:
            return
        
        payload = dialog.payload
        phone = payload["phone"]
        name = payload["name"]

        user_data = find_user_by_phone(phone)
        
        if not user_data:
            self._show_error_dialog(
                "Пользователь не найден",
                f"Контакт с номером {phone} не зарегистрирован в Ten Dem.\n\n"
                f"Попросите пользователя сначала установить приложение."
            )
            return

        contact_info = {
            'uid': user_data['uid'],
            'name': user_data.get('name', name),
            'phone': phone
        }
        
        add_contact_to_list(self.current_user.uid, contact_info)
        
        self._show_success_dialog(
            "Контакт добавлен",
            f"\"{contact_info['name']}\" успешно добавлен в ваши контакты.\n\n"
            f"Теперь вы можете начать переписку."
        )
        
        if self.current_view == "contacts":
            self.load_contacts_list()
        else:
            reply = QMessageBox.question(self, "Открыть чат?", 
                "Хотите открыть чат с этим пользователем?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.switch_view("contacts")
            self.load_contacts_list()

    def create_group(self):
        users = [user for user in get_all_users() if user.get("uid") != self.current_user.uid and not user.get("is_group")]
        dialog = CreateGroupDialog(users, self)
        if dialog.exec() != dialog.DialogCode.Accepted or not dialog.payload:
            return
        payload = dialog.payload
        uid = create_user(
            {
                "uid": f"group-{uuid.uuid4().hex[:12]}",
                "name": payload["name"],
                "phone": "",
                "username": "",
                "status": "online",
                "avatar_url": "",
                "bio": "Группа",
                "theme": "dark",
                "is_group": True,
                "member_uids": [self.current_user.uid, *payload["member_uids"]],
            }
        )
        self.load_chats()
        self._open_chat_by_uid(uid)

    def load_chats(self):
        """✅ Загружает чаты из Firebase + локального кэша"""
        self.chats_list_widget.clear()
        self.contact_widgets.clear()
        
        summaries = get_chat_summaries(self.current_user.uid)
        all_users = get_all_users()
        visible_users = [u for u in all_users if u.get('uid') != self.current_user.uid]
        chat_users = [u for u in visible_users if u.get('uid') in summaries]
        
        if not chat_users:
            print("📭 Список чатов пуст")
        
        for user_data in chat_users:
            user = User.from_dict(user_data, user_data.get('uid'))
            summary = summaries.get(user.uid, {})
            item = QListWidgetItem()
            widget = ContactItem(
                user,
                last_message=summary.get("last_message", "Начните разговор"),
                unread_count=summary.get("unread_count", 0),
                timestamp=summary.get("timestamp"),
                is_pinned=False,
                theme_name=getattr(self.current_user, "theme", "dark"),
            )
            item.setSizeHint(widget.sizeHint())
            self.chats_list_widget.addItem(item)
            self.chats_list_widget.setItemWidget(item, widget)
            self.contact_widgets[user.uid] = widget
        
        print(f"✅ Загружено {len(chat_users)} чатов")

    def load_contacts_list(self):
        self.contacts_list_widget.clear()
        self.contact_list_widgets.clear()
        
        raw_contacts = get_contacts(self.current_user.uid)
        
        if not raw_contacts:
            return

        for c_data in raw_contacts:
            uid = c_data.get('uid')
            name = c_data.get('name', 'Unknown')
            phone = c_data.get('phone', '')
            
            user = User(uid=uid, name=name, phone=phone, status="offline")
            
            item = QListWidgetItem()
            widget = ContactItem(
                user,
                last_message="Нажмите, чтобы написать",
                unread_count=0,
                timestamp=None,
                is_pinned=False,
                theme_name=getattr(self.current_user, "theme", "dark"),
            )
            item.setSizeHint(widget.sizeHint())
            self.contacts_list_widget.addItem(item)
            self.contacts_list_widget.setItemWidget(item, widget)
            self.contact_list_widgets[uid] = widget

    def filter_current_view(self, text: str):
        text = text.strip().lower()
        if self.current_view == "chats":
            list_widget = self.chats_list_widget
        else:
            list_widget = self.contacts_list_widget
            
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            widget = list_widget.itemWidget(item)
            if widget and hasattr(widget, 'user'):
                name = getattr(widget.user, 'name', '').lower()
                item.setHidden(text not in name)

    def open_chat_from_item(self, item: QListWidgetItem):
        widget = self.chats_list_widget.itemWidget(item)
        if widget:
            self._open_chat_interface(widget.user)

    def open_chat_from_contact(self, item: QListWidgetItem):
        widget = self.contacts_list_widget.itemWidget(item)
        if widget:
            self._open_chat_interface(widget.user)

    def _open_chat_by_uid(self, target_uid: str):
        for index in range(self.chats_list_widget.count()):
            item = self.chats_list_widget.item(index)
            widget = self.chats_list_widget.itemWidget(item)
            if widget and widget.user.uid == target_uid:
                self.chats_list_widget.setCurrentItem(item)
                self._open_chat_interface(widget.user)
                return

    def _open_chat_interface(self, user: User):
        if self.placeholder:
            self.placeholder.hide()
        
        if self.current_chat_widget:
            self.current_chat_widget.deleteLater()
        
        self.current_chat_widget = ChatWidget(self.current_user, user, shortcuts_map=self.shortcuts_map, parent=self.right_panel)
        self.current_chat_widget.chat_updated.connect(self.refresh_chats)
        
        layout = self.right_panel.layout()
        layout.addWidget(self.current_chat_widget)

    def refresh_chats(self, contact_uid: str = ""):
        if self.current_view == "chats":
            self.load_chats()

    def open_chat_context_menu(self, pos):
        item = self.chats_list_widget.itemAt(pos)
        if not item:
            return
        widget = self.chats_list_widget.itemWidget(item)
        if not widget:
            return

        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        info_action = menu.addAction("Информация")
        open_action = menu.addAction("Открыть чат")
        delete_action = menu.addAction("Удалить чат")
        
        action = menu.exec(self.chats_list_widget.mapToGlobal(pos))

        if action == open_action:
            self._open_chat_interface(widget.user)
        elif action == info_action:
            ContactInfoDialog(self.current_user, widget.user, self).exec()
        elif action == delete_action:
            self.delete_chat(widget.user.uid)

    def open_contact_context_menu(self, pos):
        item = self.contacts_list_widget.itemAt(pos)
        if not item:
            return
        widget = self.contacts_list_widget.itemWidget(item)
        if not widget:
            return

        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        info_action = menu.addAction("Информация")
        write_action = menu.addAction("Написать")
        delete_action = menu.addAction("Удалить контакт")
        
        action = menu.exec(self.contacts_list_widget.mapToGlobal(pos))

        if action == write_action:
            self._open_chat_interface(widget.user)
        elif action == info_action:
            ContactInfoDialog(self.current_user, widget.user, self).exec()
        elif action == delete_action:
            self.delete_contact(widget.user.uid)

    def delete_chat(self, chat_uid: str):
        """✅ Полное удаление чата из Firebase + локально + обновление UI"""
        if QMessageBox.question(self, "Удалить чат", 
            "Удалить чат из списка?\n\n⚠️ Сообщения останутся в базе данных.") != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from src.database.messages_db import delete_chat as delete_chat_record
            success = delete_chat_record(self.current_user.uid, chat_uid)
            
            # ✅ ВАЖНО: Очищаем локальные сообщения этого чата
            store = load_store()
            messages = store.get("messages", [])
            
            filtered_messages = [
                msg for msg in messages 
                if not (
                    (msg.get("from_uid") == self.current_user.uid and msg.get("to_uid") == chat_uid) or
                    (msg.get("from_uid") == chat_uid and msg.get("to_uid") == self.current_user.uid)
                )
            ]
            
            if len(filtered_messages) < len(messages):
                store["messages"] = filtered_messages
                save_store(store)
                print(f"🧹 Очищено {len(messages) - len(filtered_messages)} локальных сообщений")
            
            try:
                from src.database.local_cache import clear_messages_cache
                clear_messages_cache(chat_uid)
            except:
                pass
            
            self.load_chats()
            
            if self.current_chat_widget:
                current_chat_user = self.current_chat_widget.contact
                if current_chat_user.uid == chat_uid:
                    self.current_chat_widget.deleteLater()
                    self.current_chat_widget = None
                    self.placeholder.show()
            
            self.chats_list_widget.repaint()
            self.chats_list_widget.update()
            
            print(f"✅ Чат {chat_uid} успешно удалён")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить чат:\n{str(e)}")
            print(f"❌ Ошибка удаления чата: {e}")
            import traceback
            traceback.print_exc()

    def delete_contact(self, contact_uid: str):
        if QMessageBox.question(self, "Удалить контакт", "Удалить контакт из списка?") != QMessageBox.StandardButton.Yes:
            return
        
        db = get_db()
        if db:
            user_ref = db.collection('users').document(self.current_user.uid)
            user_doc = user_ref.get()
            if user_doc.exists:
                contacts = user_doc.to_dict().get('contacts', [])
                contacts = [c for c in contacts if c.get('uid') != contact_uid]
                user_ref.update({'contacts': contacts})
        
        self.load_contacts_list()

    def _bind_shortcuts(self):
        for shortcut in self._shortcuts:
            shortcut.deleteLater()
        self._shortcuts = []

        bindings = {
            "search": self.focus_search,
            "new_chat": self.open_create_menu,
            "escape": self.handle_escape,
        }
        for key, handler in bindings.items():
            sequence = self.shortcuts_map.get(key)
            if not sequence:
                continue
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def handle_escape(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.reject()
            return
        if self.current_chat_widget:
            self.current_chat_widget.deleteLater()
            self.current_chat_widget = None
            self.placeholder.show()

    def open_settings(self):
        self.settings_window = SettingsWindow(self.current_user, self)
        self.settings_window.settings_saved.connect(self.on_settings_saved)
        self.settings_window.exec()

    def on_settings_saved(self, settings):
        self.current_user.name = settings.get("name", self.current_user.name)
        self.current_user.username = settings.get("username", getattr(self.current_user, "username", ""))
        self.current_user.bio = settings.get("bio", getattr(self.current_user, "bio", ""))
        self.current_user.theme = settings.get("theme", getattr(self.current_user, "theme", "dark"))
        self.shortcuts_map = {**DEFAULT_SHORTCUTS, **settings.get("shortcuts", {})}
        
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            apply_theme(app, self.current_user.theme)
        
        self.colors = get_theme_colors(self.current_user.theme)
        self.setWindowTitle(f"Ten Dem | {self.current_user.name}")
        
        self.setStyleSheet(f"QMainWindow {{ background-color: {self.colors['bg_primary']}; }}")
        self.centralWidget().setStyleSheet(f"#mainSurface {{ background-color: {self.colors['bg_primary']}; }}")
        
        self.load_chats()
        if self.current_view == "contacts":
            self.load_contacts_list()
        
        store = load_store()
        store.setdefault("settings", {})[self.current_user.uid] = {
            "theme": self.current_user.theme,
            "shortcuts": self.shortcuts_map,
        }
        save_store(store)

    def _shadow_color(self):
        from PyQt6.QtGui import QColor
        return QColor(68, 148, 74, 50)

    def _std_icon(self, name: str):
        pixmap = getattr(QStyle.StandardPixmap, name, None)
        if pixmap is None:
            return QIcon()
        return self.style().standardIcon(pixmap)

    def _menu_style(self):
        return f"""
        QMenu {{
            background-color: {self.colors['bg_secondary']};
            color: {self.colors['text_primary']};
            border: none;
            border-radius: 20px;
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

    def _show_success_dialog(self, title: str, message: str):
        """✅ Показывает красивое окно успеха"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 20px;
            }}
            QLabel {{
                color: {self.colors['text_primary']};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
                border: none;
                border-radius: 12px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        icon_label = QLabel("✅")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {self.colors['text_primary']};")
        layout.addWidget(title_label)
        
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"font-size: 13px; color: {self.colors['text_secondary']};")
        layout.addWidget(message_label)
        
        btn = QPushButton("Готово")
        btn.clicked.connect(dialog.accept)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn)
        
        dialog.exec()

    def _show_error_dialog(self, title: str, message: str):
        """❌ Показывает красивое окно ошибки"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(400, 200)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 20px;
            }}
            QLabel {{
                color: {self.colors['text_primary']};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        icon_label = QLabel("⚠️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {self.colors['text_primary']};")
        layout.addWidget(title_label)
        
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"font-size: 13px; color: {self.colors['text_secondary']};")
        layout.addWidget(message_label)
        
        btn = QPushButton("Понятно")
        btn.clicked.connect(dialog.accept)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(btn)
        
        dialog.exec()

    def closeEvent(self, event):
        set_online_status(self.current_user.uid, "offline")
        event.accept()