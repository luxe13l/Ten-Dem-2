"""Theme manager and application stylesheet helpers."""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.styles.colors import LIGHT_COLORS
from src.styles.colors import (
    ACCENT_HOVER,
    ACCENT_PRESSED,
    ACCENT_PRIMARY,
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    DELIVERED_CHECK,
    DIVIDER,
    ERROR,
    ICON_ACTIVE,
    ICON_DEFAULT,
    ICON_HOVER,
    INPUT_BORDER,
    INPUT_BORDER_FOCUS,
    MESSAGE_OTHER_BG,
    MESSAGE_OWN_BG,
    OFFLINE,
    ONLINE,
    READ_CHECK,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    WARNING,
    MESSAGE_OTHER_TEXT,
    MESSAGE_OWN_TEXT,
)


class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
        self.colors = self._get_dark_theme()

    def _get_dark_theme(self):
        return {
            "bg_primary": BG_PRIMARY,
            "bg_secondary": BG_SECONDARY,
            "bg_tertiary": BG_TERTIARY,
            "accent_primary": ACCENT_PRIMARY,
            "accent_hover": ACCENT_HOVER,
            "accent_pressed": ACCENT_PRESSED,
            "text_primary": TEXT_PRIMARY,
            "text_secondary": TEXT_SECONDARY,
            "text_tertiary": TEXT_TERTIARY,
            "message_own_bg": MESSAGE_OWN_BG,
            "message_own_text": MESSAGE_OWN_TEXT,
            "message_other_bg": MESSAGE_OTHER_BG,
            "message_other_text": MESSAGE_OTHER_TEXT,
            "online": ONLINE,
            "offline": OFFLINE,
            "divider": DIVIDER,
            "input_border": INPUT_BORDER,
            "input_border_focus": INPUT_BORDER_FOCUS,
            "icon_default": ICON_DEFAULT,
            "icon_hover": ICON_HOVER,
            "icon_active": ICON_ACTIVE,
            "success": SUCCESS,
            "error": ERROR,
            "warning": WARNING,
            "read_check": READ_CHECK,
            "delivered_check": DELIVERED_CHECK,
        }

    def set_theme(self, theme_name: str):
        theme_name = (theme_name or "dark").lower()
        if theme_name == "light":
            self.current_theme = "light"
            self.colors = LIGHT_COLORS.copy()
            self.colors.setdefault("accent_primary", ACCENT_PRIMARY)
            self.colors.setdefault("accent_hover", ACCENT_HOVER)
            self.colors.setdefault("divider", "#E5E7EB")
        else:
            self.current_theme = "dark"
            self.colors = self._get_dark_theme()
        self.theme_changed.emit(self.current_theme)

    def get_color(self, name: str) -> str:
        return self.colors.get(name, "#000000")

    def is_dark(self) -> bool:
        return self.current_theme == "dark"


theme_manager = ThemeManager()


def build_app_stylesheet(theme_name: str) -> str:
    theme_manager.set_theme(theme_name)
    bg = theme_manager.get_color("bg_primary")
    panel = theme_manager.get_color("bg_secondary")
    input_bg = theme_manager.get_color("bg_tertiary")
    text = theme_manager.get_color("text_primary")
    secondary = theme_manager.get_color("text_secondary")
    divider = theme_manager.get_color("divider")
    accent = theme_manager.get_color("accent_primary")
    return f"""
    QWidget {{
        color: {text};
    }}
    QMainWindow, QDialog {{
        background-color: {bg};
    }}
    QLabel {{
        background-color: transparent;
        color: {text};
    }}
    QFrame {{
        background-color: transparent;
    }}
    QLineEdit, QTextEdit, QComboBox, QListWidget, QScrollArea {{
        background-color: {input_bg};
        color: {text};
        border: none;
        selection-background-color: {accent};
    }}
    QPushButton {{
        color: {text};
    }}
    QMenu {{
        background-color: {panel};
        color: {text};
        border: none;
        border-radius: 14px;
    }}
    QMenu::item:selected {{
        background-color: {input_bg};
    }}
    QCheckBox {{
        color: {text};
    }}
    QCheckBox::indicator {{
        background-color: {input_bg};
        border: 1px solid {divider};
    }}
    QCheckBox::indicator:checked {{
        background-color: {accent};
        border: 1px solid {accent};
    }}
    """


def apply_theme(app, theme_name: str):
    if app is None:
        return
    app.setStyleSheet(build_app_stylesheet(theme_name))


def get_theme_colors(theme_name: str | None = None) -> dict:
    previous = theme_manager.current_theme
    if theme_name:
        theme_manager.set_theme(theme_name)
    colors = dict(theme_manager.colors)
    if theme_name:
        theme_manager.set_theme(previous)
    colors.setdefault("bg_primary", BG_PRIMARY)
    colors.setdefault("bg_secondary", BG_SECONDARY)
    colors.setdefault("bg_tertiary", BG_TERTIARY)
    colors.setdefault("text_primary", TEXT_PRIMARY)
    colors.setdefault("text_secondary", TEXT_SECONDARY)
    colors.setdefault("text_tertiary", TEXT_TERTIARY)
    colors.setdefault("accent_primary", ACCENT_PRIMARY)
    colors.setdefault("divider", DIVIDER)
    colors.setdefault("message_own_bg", MESSAGE_OWN_BG)
    colors.setdefault("message_own_text", MESSAGE_OWN_TEXT)
    colors.setdefault("message_other_bg", MESSAGE_OTHER_BG)
    colors.setdefault("message_other_text", MESSAGE_OTHER_TEXT)
    colors.setdefault("icon_default", ICON_DEFAULT)
    colors.setdefault("icon_hover", ICON_HOVER)
    colors.setdefault("online", ONLINE)
    return colors
