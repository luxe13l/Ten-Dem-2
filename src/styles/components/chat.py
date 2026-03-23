"""
Стили чата Ten Dem
Отвечает: [Имя друга]
"""
from src.styles.colors import (
    BG_SECONDARY, BG_PRIMARY, DIVIDER,
    ACCENT_PRIMARY, TEXT_PRIMARY
)
from src.styles.tokens import PADDING_CARD, AVATAR_CHAT
from src.styles.fonts import FONT_FAMILY


def get_chat_header_style():
    """Шапка чата."""
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border-bottom: 1px solid {DIVIDER};
        }}
    """


def get_chat_input_panel_style():
    """Панель ввода."""
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border-top: 1px solid {DIVIDER};
        }}
    """