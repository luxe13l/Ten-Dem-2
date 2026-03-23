"""
Стили кнопок Ten Dem
Отвечает: [Имя друга]
"""
from src.styles.colors import (
    ACCENT_PRIMARY, ACCENT_HOVER, ACCENT_PRESSED,
    TEXT_ON_ACCENT, BG_TERTIARY, ICON_DEFAULT, ICON_HOVER
)
from src.styles.tokens import RADIUS_BUTTON, PADDING_ELEMENT


def get_button_primary_style():
    """Основная кнопка (фиолетовая)."""
    return f"""
        QPushButton {{
            background-color: {ACCENT_PRIMARY};
            color: {TEXT_ON_ACCENT};
            border: none;
            border-radius: {RADIUS_BUTTON}px;
            padding: {PADDING_ELEMENT}px 24px;
            font-size: 15px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {ACCENT_PRESSED};
        }}
    """


def get_button_secondary_style():
    """Вторичная кнопка (серая)."""
    return f"""
        QPushButton {{
            background-color: {BG_TERTIARY};
            color: {TEXT_ON_ACCENT};
            border: none;
            border-radius: {RADIUS_BUTTON}px;
            padding: {PADDING_ELEMENT}px 24px;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background-color: #2A2A2A;
        }}
    """


def get_button_icon_style():
    """Кнопка-иконка."""
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            color: {ICON_DEFAULT};
            font-size: 20px;
        }}
        QPushButton:hover {{
            background-color: {BG_TERTIARY};
            color: {ICON_HOVER};
            border-radius: 8px;
        }}
    """