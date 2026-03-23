"""
Стили сообщений Ten Dem
Отвечает: [Имя друга]
"""
from src.styles.colors import (
    MESSAGE_OWN_BG, MESSAGE_OWN_TEXT,
    MESSAGE_OTHER_BG, MESSAGE_OTHER_TEXT,
    MESSAGE_TIME, TEXT_TERTIARY, TEXT_ON_ACCENT
)
from src.styles.tokens import RADIUS_MESSAGE, PADDING_CARD
from src.styles.fonts import FONT_FAMILY


def get_message_own_style():
    """Своё сообщение (фиолетовое)."""
    return f"""
        QFrame {{
            background-color: {MESSAGE_OWN_BG};
            color: {MESSAGE_OWN_TEXT};
            border-radius: {RADIUS_MESSAGE}px;
            padding: {PADDING_CARD}px;
        }}
        QLabel {{
            color: {MESSAGE_OWN_TEXT};
            font-family: {FONT_FAMILY};
        }}
    """


def get_message_other_style():
    """Чужое сообщение (серое)."""
    return f"""
        QFrame {{
            background-color: {MESSAGE_OTHER_BG};
            color: {MESSAGE_OTHER_TEXT};
            border-radius: {RADIUS_MESSAGE}px;
            padding: {PADDING_CARD}px;
        }}
        QLabel {{
            color: {MESSAGE_OTHER_TEXT};
            font-family: {FONT_FAMILY};
        }}
    """