"""Settings dialog with theme-aware styling."""
from __future__ import annotations
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from src.database.auth_manager import auth_manager
from src.database.local_store import load_store, save_store
from src.database.users_db import update_user
from src.styles import FONT_FAMILY, RADIUS_BUTTON, RADIUS_CARD
from src.styles.themes import apply_theme, get_theme_colors
from src.ui.auto_hide_scrollbar import AutoHideScrollBar

DEFAULT_SHORTCUTS = {
    "send": "Ctrl+Return",
    "search": "Ctrl+F",
    "new_chat": "Ctrl+N",
    "escape": "Esc",
}

class SettingsWindow(QDialog):
    settings_saved = pyqtSignal(dict)
    
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.colors = get_theme_colors(getattr(self.current_user, "theme", "dark"))
        self.is_light = getattr(self.current_user, "theme", "dark") == "light"
        self.form_controls = {}
        self.settings = self._load_settings()
        self.init_ui()

    def _load_settings(self):
        defaults = {
            "name": self.current_user.name,
            "username": getattr(self.current_user, "username", ""),
            "bio": getattr(self.current_user, "bio", ""),
            "theme": getattr(self.current_user, "theme", "dark"),
            "font_scale": 15,
            "sound": True,
            "push": True,
            "preview": True,
            "dnd": False,
            "shortcuts": DEFAULT_SHORTCUTS.copy(),
        }
        data = load_store().get("settings", {}).get(self.current_user.uid, {})
        merged = dict(defaults)
        merged.update(data)
        merged["shortcuts"] = {**DEFAULT_SHORTCUTS, **data.get("shortcuts", {})}
        return merged

    def _tone(self, dark_value: str, light_value: str) -> str:
        return light_value if self.is_light else dark_value

    def init_ui(self):
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(820, 640)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("settingsCard")
        card.setStyleSheet(
            f"""
            QFrame#settingsCard {{
                background-color: {self._tone('#0E1115', '#FFFFFF')};
                border: 1px solid {self._tone('#181C21', '#E3E6EB')};
                border-radius: 34px;
            }}
            """
        )
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._create_header())
        layout.addWidget(self._create_content(), 1)
        layout.addWidget(self._create_footer())

    def _create_header(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {self._tone('#14181D', '#F4F6F9')}; border-radius: 34px 34px 0 0; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(26, 22, 26, 22)

        title = QLabel("Настройки")
        title.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 22px; font-weight: 600;")
        layout.addWidget(title)
        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(38, 38)
        close_btn.setStyleSheet(self._icon_style())
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        return frame

    def _create_content(self):
        scroll = QScrollArea()
        scroll.setVerticalScrollBar(AutoHideScrollBar(parent=scroll))
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ width: 8px; background: transparent; margin: 10px 4px 10px 0; }}
            QScrollBar::handle:vertical {{ background: {self._tone('rgba(255,255,255,0.18)', 'rgba(19,32,44,0.18)')}; border-radius: 999px; min-height: 34px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; border: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
            """
        )

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(self._profile_section())
        layout.addWidget(self._appearance_section())
        layout.addWidget(self._notifications_section())
        layout.addWidget(self._privacy_section())
        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _profile_section(self):
        section, layout = self._section("Профиль")

        row = QHBoxLayout()
        avatar = QLabel((self.current_user.name or "?")[0].upper())
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(72, 72)
        avatar.setStyleSheet(
            f"QLabel {{ background-color: {self.colors['accent_primary']}; color: white; border-radius: 36px; font-size: 28px; font-weight: 700; }}"
        )
        row.addWidget(avatar)

        text_layout = QVBoxLayout()
        name_label = QLabel(self.current_user.name or "Пользователь")
        name_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 18px; font-weight: 600;")
        text_layout.addWidget(name_label)
        phone_label = QLabel(self.current_user.phone or "")
        phone_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
        text_layout.addWidget(phone_label)
        row.addLayout(text_layout)
        row.addStretch()
        layout.addLayout(row)

        self.form_controls["name"] = self._line_edit(self.settings.get("name", self.current_user.name), "Имя")
        self.form_controls["username"] = self._line_edit(
            self.settings.get("username", getattr(self.current_user, "username", "")),
            "@username",
        )
        self.form_controls["bio"] = self._line_edit(
            self.settings.get("bio", getattr(self.current_user, "bio", "")),
            "О себе",
        )
        layout.addWidget(self.form_controls["name"])
        layout.addWidget(self.form_controls["username"])
        layout.addWidget(self.form_controls["bio"])
        return section

    def _appearance_section(self):
        section, layout = self._section("Оформление")

        row = QHBoxLayout()
        label = QLabel("Тема")
        label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 14px;")
        row.addWidget(label)
        row.addStretch()

        combo = QComboBox()
        combo.addItems(["Тёмная", "Светлая", "Системная"])
        combo.setCurrentText({"dark": "Тёмная", "light": "Светлая", "system": "Системная"}.get(self.settings.get("theme", "dark"), "Тёмная"))
        combo.setStyleSheet(self._input_style())
        self.form_controls["theme"] = combo
        row.addWidget(combo)
        layout.addLayout(row)

        slider_label = QLabel("Размер текста")
        slider_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 14px;")
        layout.addWidget(slider_label)

        groove = self._tone("#232830", "#D9E0E7")
        handle = self._tone("#5F6D7C", "#6E8FB2")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(12)
        slider.setMaximum(20)
        slider.setValue(int(self.settings.get("font_scale", 15)))
        slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{ height: 6px; background: {groove}; border-radius: 3px; }}
            QSlider::handle:horizontal {{ width: 16px; margin: -5px 0; border-radius: 8px; background: {handle}; }}
            QSlider::sub-page:horizontal {{ background: {handle}; border-radius: 3px; }}
            """
        )
        self.form_controls["font_scale"] = slider
        layout.addWidget(slider)
        return section

    def _notifications_section(self):
        section, layout = self._section("Уведомления")
        indicator_bg = self._tone("#10151B", "#F0F3F6")
        for key, title in [
            ("sound", "Звук сообщений"),
            ("push", "Push-уведомления"),
            ("preview", "Показывать текст"),
            ("dnd", "Не беспокоить"),
        ]:
            box = QCheckBox(title)
            box.setChecked(bool(self.settings.get(key, False)))
            box.setStyleSheet(
                f"""
                QCheckBox {{ color: {self.colors['text_primary']}; font-size: 14px; spacing: 10px; }}
                QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {self.colors['divider']}; background: {indicator_bg}; }}
                QCheckBox::indicator:checked {{ background-color: {self.colors['accent_primary']}; border-color: {self.colors['accent_primary']}; }}
                """
            )
            self.form_controls[key] = box
            layout.addWidget(box)
        return section

    def _privacy_section(self):
        section, layout = self._section("Конфиденциальность")
        for left, right in [
            ("Кто видит онлайн", "Все"),
            ("Кто может писать", "Все"),
            ("Кто может звонить", "Контакты"),
        ]:
            row = QHBoxLayout()
            left_label = QLabel(left)
            left_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 14px;")
            row.addWidget(left_label)
            row.addStretch()
            right_label = QLabel(right)
            right_label.setStyleSheet(f"color: {self.colors['text_secondary']}; font-size: 13px;")
            row.addWidget(right_label)
            layout.addLayout(row)
        return section

    def _create_footer(self):
        frame = QFrame()
        # ИСПРАВЛЕНО: нижние углы теперь закруглены
        frame.setStyleSheet(
            f"QFrame {{ background-color: {self._tone('#14181D', '#F4F6F9')}; border-radius: 0 0 34px 34px; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.addStretch()

        cancel = QPushButton("Отмена")
        cancel.setFixedSize(120, 44)
        cancel.setStyleSheet(self._secondary_button_style())
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)

        save = QPushButton("Сохранить")
        save.setFixedSize(140, 44)
        save.setStyleSheet(self._primary_button_style())
        save.clicked.connect(self.on_save)
        layout.addWidget(save)
        return frame

    def on_save(self):
        raw_username = self.form_controls["username"].text().strip()
        if raw_username:
            available, result = auth_manager.check_username_available(raw_username, exclude_uid=self.current_user.uid)
            if not available:
                QMessageBox.warning(self, "Username", result)
                return
            raw_username = result

        payload = {
            "name": self.form_controls["name"].text().strip() or self.current_user.name,
            "username": raw_username,
            "bio": self.form_controls["bio"].text().strip(),
            "theme": {"Тёмная": "dark", "Светлая": "light", "Системная": "system"}.get(self.form_controls["theme"].currentText(), "dark"),
            "font_scale": self.form_controls["font_scale"].value(),
            "sound": self.form_controls["sound"].isChecked(),
            "push": self.form_controls["push"].isChecked(),
            "preview": self.form_controls["preview"].isChecked(),
            "dnd": self.form_controls["dnd"].isChecked(),
            "shortcuts": DEFAULT_SHORTCUTS.copy(),
        }
        store = load_store()
        store.setdefault("settings", {})[self.current_user.uid] = payload
        save_store(store)

        self.current_user.name = payload["name"]
        self.current_user.username = payload["username"]
        self.current_user.bio = payload["bio"]
        self.current_user.theme = payload["theme"]

        update_user(
            self.current_user.uid,
            {
                "name": payload["name"],
                "username": payload["username"],
                "bio": payload["bio"],
                "theme": payload["theme"],
            },
        )
        apply_theme(QApplication.instance(), payload["theme"])
        self.settings_saved.emit(payload)
        self.accept()

    def _section(self, title: str):
        section = QFrame()
        section.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self._tone('#171C22', '#F7F8FA')};
                border: 1px solid {self._tone('transparent', '#E7EAEE')};
                border-radius: {RADIUS_CARD + 6}px;
            }}
            """
        )
        layout = QVBoxLayout(section)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        label = QLabel(title)
        label.setStyleSheet(f"color: {self.colors['text_primary']}; font-size: 16px; font-weight: 600;")
        layout.addWidget(label)
        return section, layout

    def _line_edit(self, value: str, placeholder: str):
        field = QLineEdit(value)
        field.setPlaceholderText(placeholder)
        field.setStyleSheet(self._input_style())
        return field

    def _input_style(self):
        bg = self._tone("#10151B", "#FFFFFF")
        border = self._tone("transparent", "#E3E7EC")
        return f"""
        QLineEdit, QComboBox {{
            background-color: {bg};
            color: {self.colors['text_primary']};
            border: 1px solid {border};
            border-radius: {RADIUS_BUTTON + 4}px;
            padding: 13px 15px;
            font-size: 14px;
            font-family: {FONT_FAMILY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            background: transparent;
        }}
        """

    def _primary_button_style(self):
        return f"""
        QPushButton {{
            background-color: {self.colors['accent_primary']};
            color: {'white' if not self.is_light else '#FFFFFF'};
            border: none;
            border-radius: {RADIUS_BUTTON + 6}px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {self.colors['accent_hover']};
        }}
        """

    def _secondary_button_style(self):
        hover_bg = self._tone("#1A1F26", "#EEF2F6")
        return f"""
        QPushButton {{
            background-color: transparent;
            color: {self.colors['text_secondary']};
            border: none;
            border-radius: {RADIUS_BUTTON + 6}px;
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            color: {self.colors['text_primary']};
        }}
        """

    def _icon_style(self):
        hover_bg = self._tone("#1A1F26", "#EEF2F6")
        return f"""
        QPushButton {{
            background-color: transparent;
            color: {self.colors['text_secondary']};
            border: none;
            border-radius: 16px;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            color: {self.colors['text_primary']};
        }}
        """