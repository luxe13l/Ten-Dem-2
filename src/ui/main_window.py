"""Main messenger window."""
from __future__ import annotations
import uuid
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut
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
    QStyle,
    QVBoxLayout,
    QWidget,
)
from src.database.local_store import load_store, save_store
from src.database.messages_db import get_chat_summaries
from src.database.users_db import create_user, get_all_users, set_online_status
from src.models.user import User
from src.styles import FONT_FAMILY, LEFT_PANEL_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from src.styles.themes import get_theme_colors
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
        self.logo_path = "Логотип Ten Dem.png"
        self.current_chat_widget = None
        self.settings_window = None
        self.contact_widgets = {}
        self.shortcuts_map = self._load_shortcuts()
        self._shortcuts: list[QShortcut] = []
        self._pending_settings = None
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
        layout.addWidget(self._create_nav_shell())
        layout.addWidget(self._create_right_panel(), 1)

    def _create_nav_shell(self):
        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(14)
        shell_layout.addWidget(self._create_nav_rail())
        shell_layout.addWidget(self._create_sidebar())
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
        
        self.nav_buttons = [
            self._rail_button(self._std_icon("SP_FileDialogContentsView"), active=True),
            self._rail_button(self._std_icon("SP_FileDialogDetailedView")),
            self._rail_button(self._std_icon("SP_DirIcon")),
        ]
        
        for btn in self.nav_buttons:
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addStretch()
        settings_btn = self._rail_button(QIcon("assets/icons/settings.svg"))
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        return rail

    def _create_sidebar(self):
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
        header.setContentsMargins(24, 24, 24, 8)
 
        title = QLabel("Чаты")
        title.setFont(QFont(FONT_FAMILY, 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.colors['text_primary']};")
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        subtitle = QLabel((getattr(self.current_user, "username", "") or self.current_user.name or "ten dem").lower())
        subtitle.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px; padding: 0 24px 10px 24px;")
        layout.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск")
        self.search_input.textChanged.connect(self.filter_contacts)
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

        self.contacts_list = QListWidget()
        self.contacts_list.setVerticalScrollBar(AutoHideScrollBar(parent=self.contacts_list))
        self.contacts_list.itemClicked.connect(self.open_chat)
        self.contacts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contacts_list.customContextMenuRequested.connect(self.open_contact_menu)
        self.contacts_list.setStyleSheet(
            f"""
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
            QListWidget::item:selected {{
                background-color: transparent;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                background: transparent;
                margin: 10px 6px 76px 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255,255,255,0.18);
                border-radius: 999px;
                min-height: 42px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: transparent;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            """
        )
        layout.addWidget(self.contacts_list, 1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(18, 0, 18, 26)
        bottom.addStretch()

        # ✅ ИСПРАВЛЕНО: Кнопка идеально круглая
        self.new_chat_button = QPushButton()
        self.new_chat_button.setFixedSize(48, 48)
        self.new_chat_button.setIcon(QIcon("assets/icons/plus.svg"))
        self.new_chat_button.setIconSize(QSize(18, 18))
        self.new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors['accent_primary']};
                color: #0D0D0D;
                border: none;
                border-radius: 999px; /* ЖЕСТКИЙ КРУГ */
            }}
            QPushButton:hover {{
                background-color: {self.colors['accent_hover']};
            }}
            """
        )
        shadow = QGraphicsDropShadowEffect(self.new_chat_button)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.transparent)
        shadow.setColor(self._shadow_color())
        self.new_chat_button.setGraphicsEffect(shadow)
        self.new_chat_button.clicked.connect(self.open_create_menu)
        bottom.addWidget(self.new_chat_button, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(bottom)
        return panel

    def _create_right_panel(self):
        self.right_panel = QWidget()
        self.right_panel.setObjectName("chatPanel")
        self.right_panel.setStyleSheet(
            f"""
            QWidget#chatPanel {{
                background-color: {self.colors['bg_secondary']};
                border-radius: 30px;
                border: 1px solid {self.colors['divider']};
            }}
            """
        )
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.placeholder = self._build_placeholder()
        right_layout.addWidget(self.placeholder)
        return self.right_panel

    def _build_placeholder(self):
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Выберите чат, чтобы начать общение")
        label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 18px;")
        layout.addWidget(label)
        return placeholder

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

    def _std_icon(self, name: str):
        pixmap = getattr(QStyle.StandardPixmap, name, None)
        if pixmap is None:
            return QIcon()
        return self.style().standardIcon(pixmap)

    def _rail_button(self, icon: QIcon, active: bool = False):
        button = QPushButton()
        button.setFixedSize(44, 44)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(icon)
        button.setIconSize(QSize(18, 18))
        background = "rgba(68, 148, 74, 0.10)" if active else "transparent"
        foreground = self.colors["accent_primary"] if active else self.colors["icon_default"]
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {background};
                color: {foreground};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {'rgba(68, 148, 74, 0.14)' if active else self.colors['bg_tertiary']};
                color: {self.colors['accent_primary'] if active else self.colors['icon_hover']};
            }}
            """
        )
        button.clicked.connect(lambda checked, btn=button: self._on_nav_clicked(btn))
        return button

    def _on_nav_clicked(self, clicked_btn):
        for btn in self.nav_buttons:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors['icon_default']};
                    border: none;
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['bg_tertiary']};
                    color: {self.colors['icon_hover']};
                }}
                """
            )
        clicked_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(68, 148, 74, 0.10);
                color: {self.colors['accent_primary']};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(68, 148, 74, 0.14);
                color: {self.colors['accent_primary']};
            }}
            """
        )

    def _shadow_color(self):
        from PyQt6.QtGui import QColor
        return QColor(68, 148, 74, 50)

    def open_create_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        contact_action = menu.addAction("Создать контакт")
        group_action = menu.addAction("Создать группу")
        contact_action.setIcon(self._std_icon("SP_FileIcon"))
        group_action.setIcon(self._std_icon("SP_FileDialogNewFolder"))
        anchor = self.new_chat_button.mapToGlobal(self.new_chat_button.rect().topLeft())
        action = menu.exec(anchor)
        if action == contact_action:
            self.create_contact()
        elif action == group_action:
            self.create_group()

    def create_contact(self):
        dialog = CreateContactDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted or not dialog.payload:
            return
        payload = dialog.payload
        uid = create_user(
            {
                "uid": f"user-{uuid.uuid4().hex[:12]}",
                "name": payload["name"],
                "phone": payload["phone"],
                "username": "",
                "status": "offline",
                "avatar_url": "",
                "bio": "",
                "theme": "dark",
                "is_group": False,
            }
        )
        self.load_contacts()
        self._open_chat_by_uid(uid)

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
        self.load_contacts()
        self._open_chat_by_uid(uid)

    def _open_chat_by_uid(self, target_uid: str):
        for index in range(self.contacts_list.count()):
            item = self.contacts_list.item(index)
            widget = self.contacts_list.itemWidget(item)
            if widget and widget.user.uid == target_uid:
                self.contacts_list.setCurrentItem(item)
                self.open_chat(item)
                return

    def handle_escape(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.reject()
            return
        if self.current_chat_widget:
            widget = self.current_chat_widget
            self.current_chat_widget = None
            try:
                self.right_panel.layout().removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()
            except RuntimeError:
                pass
            self.placeholder = self._build_placeholder()
            self.right_panel.layout().addWidget(self.placeholder)

    def open_settings(self):
        self.settings_window = SettingsWindow(self.current_user, self)
        self.settings_window.settings_saved.connect(self.on_settings_saved)
        self.settings_window.exec()

    def on_settings_saved(self, settings):
        self._pending_settings = dict(settings)
        QTimer.singleShot(0, self._apply_pending_settings)

    def _apply_pending_settings(self):
        if not self._pending_settings:
            return
        settings = dict(self._pending_settings)
        self._pending_settings = None
        self.current_user.name = settings.get("name", self.current_user.name)
        self.current_user.username = settings.get("username", getattr(self.current_user, "username", ""))
        self.current_user.bio = settings.get("bio", getattr(self.current_user, "bio", ""))
        self.current_user.theme = settings.get("theme", getattr(self.current_user, "theme", "dark"))
        self.shortcuts_map = {**DEFAULT_SHORTCUTS, **settings.get("shortcuts", {})}
        self.colors = get_theme_colors(self.current_user.theme)
        self.setWindowTitle(f"Ten Dem | {self.current_user.name}")
        old = self.takeCentralWidget()
        if old:
            old.deleteLater()
        self.current_chat_widget = None
        self.placeholder = None
        self.init_ui()
        self.load_contacts()
        self._bind_shortcuts()

    def load_contacts(self):
        self.contacts_list.clear()
        self.contact_widgets.clear()
        summaries = get_chat_summaries(self.current_user.uid)
        store = load_store()
        pinned = set(store.get("pinned_chats", {}).get(self.current_user.uid, []))
        archived = set(store.get("archived_chats", {}).get(self.current_user.uid, []))
        deleted = set(store.get("deleted_chats", {}).get(self.current_user.uid, []))

        all_users = get_all_users()
        visible_users = [
            user
            for user in all_users
            if user.get("uid") != self.current_user.uid and user.get("uid") not in archived and user.get("uid") not in deleted
        ]
        visible_users.sort(
            key=lambda user: (
                0 if user.get("uid") in pinned else 1,
                -(summaries.get(user.get("uid"), {}).get("timestamp").timestamp() if summaries.get(user.get("uid"), {}).get("timestamp") else 0),
                (user.get("name") or "").lower(),
            )
        )

        for user_data in visible_users:
            user = User.from_dict(user_data, user_data.get("uid"))
            summary = summaries.get(user.uid, {})
            item = QListWidgetItem()
            widget = ContactItem(
                user,
                last_message=summary.get("last_message", "Начните разговор"),
                unread_count=summary.get("unread_count", 0),
                timestamp=summary.get("timestamp"),
                is_pinned=user.uid in pinned,
                theme_name=getattr(self.current_user, "theme", "dark"),
            )
            item.setSizeHint(widget.sizeHint())
            self.contacts_list.addItem(item)
            self.contacts_list.setItemWidget(item, widget)
            self.contact_widgets[user.uid] = widget

    def filter_contacts(self, text: str):
        text = text.strip().lower()
        for index in range(self.contacts_list.count()):
            item = self.contacts_list.item(index)
            widget = self.contacts_list.itemWidget(item)
            name = getattr(getattr(widget, "user", None), "name", "").lower()
            username = getattr(getattr(widget, "user", None), "username", "").lower()
            item.setHidden(text not in name and text not in username)

    def open_chat(self, item: QListWidgetItem):
        contact_widget = self.contacts_list.itemWidget(item)
        if not contact_widget:
            return
        
        # Сброс выделения со всех
        for index in range(self.contacts_list.count()):
            prev_item = self.contacts_list.item(index)
            prev_widget = self.contacts_list.itemWidget(prev_item)
            if prev_widget and hasattr(prev_widget, 'set_selected'):
                prev_widget.set_selected(False)
        
        # Выделение текущего
        if hasattr(contact_widget, 'set_selected'):
            contact_widget.set_selected(True)
        
        if self.placeholder is not None:
            self.right_panel.layout().removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None
        if self.current_chat_widget is not None:
            widget = self.current_chat_widget
            self.current_chat_widget = None
            try:
                self.right_panel.layout().removeWidget(widget)
                widget.setParent(None)
                widget.deleteLater()
            except RuntimeError:
                pass
        self.current_chat_widget = ChatWidget(self.current_user, contact_widget.user, shortcuts_map=self.shortcuts_map, parent=self.right_panel)
        self.current_chat_widget.chat_updated.connect(self.refresh_contacts)
        self.right_panel.layout().addWidget(self.current_chat_widget)

    def refresh_contacts(self, contact_uid: str = ""):
        if not contact_uid or contact_uid not in self.contact_widgets:
            self.load_contacts()
            return
        summary = get_chat_summaries(self.current_user.uid).get(contact_uid, {})
        widget = self.contact_widgets.get(contact_uid)
        if widget:
            widget.update_preview(
                last_message=summary.get("last_message", widget.last_message),
                timestamp=summary.get("timestamp", widget.timestamp),
                unread_count=summary.get("unread_count", widget.unread_count),
            )

    def open_contact_menu(self, pos):
        item = self.contacts_list.itemAt(pos)
        if not item:
            return
        widget = self.contacts_list.itemWidget(item)
        if not widget:
            return

        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        info_action = menu.addAction("Информация")
        open_action = menu.addAction("Открыть чат")
        info_action.setIcon(self._std_icon("SP_MessageBoxInformation"))
        open_action.setIcon(self._std_icon("SP_DialogOpenButton"))

        store = load_store()
        pinned = set(store.get("pinned_chats", {}).get(self.current_user.uid, []))
        archived = set(store.get("archived_chats", {}).get(self.current_user.uid, []))

        pin_action = menu.addAction("Открепить чат" if widget.user.uid in pinned else "Закрепить чат")
        archive_action = menu.addAction("Вернуть из архива" if widget.user.uid in archived else "Архивировать чат")
        delete_action = menu.addAction("Удалить чат")
        pin_action.setIcon(QIcon("assets/icons/attach.svg"))
        archive_action.setIcon(self._std_icon("SP_DialogSaveButton"))
        delete_action.setIcon(self._std_icon("SP_TrashIcon"))
        action = menu.exec(self.contacts_list.mapToGlobal(pos))

        if action == open_action:
            self.open_chat(item)
        elif action == info_action:
            ContactInfoDialog(self.current_user, widget.user, self).exec()
        elif action == pin_action:
            self.toggle_pin_chat(widget.user.uid)
        elif action == archive_action:
            self.toggle_archive_chat(widget.user.uid)
        elif action == delete_action:
            self.delete_chat(widget.user.uid)

    def toggle_pin_chat(self, chat_uid: str):
        store = load_store()
        pinned = set(store.get("pinned_chats", {}).get(self.current_user.uid, []))
        if chat_uid in pinned:
            pinned.remove(chat_uid)
        else:
            pinned.add(chat_uid)
        store.setdefault("pinned_chats", {})[self.current_user.uid] = sorted(pinned)
        save_store(store)
        self.load_contacts()

    def toggle_archive_chat(self, chat_uid: str):
        store = load_store()
        archived = set(store.get("archived_chats", {}).get(self.current_user.uid, []))
        if chat_uid in archived:
            archived.remove(chat_uid)
        else:
            archived.add(chat_uid)
        store.setdefault("archived_chats", {})[self.current_user.uid] = sorted(archived)
        save_store(store)
        if self.current_chat_widget and self.current_chat_widget.contact.uid == chat_uid and chat_uid in archived:
            self.handle_escape()
        self.load_contacts()

    def delete_chat(self, chat_uid: str):
        if QMessageBox.question(self, "Удалить чат", "Удалить чат из списка?") != QMessageBox.StandardButton.Yes:
            return
        store = load_store()
        deleted = set(store.get("deleted_chats", {}).get(self.current_user.uid, []))
        deleted.add(chat_uid)
        store.setdefault("deleted_chats", {})[self.current_user.uid] = sorted(deleted)
        save_store(store)
        if self.current_chat_widget and self.current_chat_widget.contact.uid == chat_uid:
            self.handle_escape()
        self.load_contacts()

    def _icon_button_style(self):
        return f"""
        QPushButton {{
            background-color: transparent;
            color: {self.colors['icon_default']};
            border: none;
            border-radius: 999px;
        }}
        QPushButton:hover {{
            background-color: {self.colors['bg_tertiary']};
            color: {self.colors['text_primary']};
        }}
        """

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

    def closeEvent(self, event):
        set_online_status(self.current_user.uid, "offline")
        event.accept()