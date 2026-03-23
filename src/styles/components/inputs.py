"""
Стили полей ввода Ten Dem
Отвечает: [Имя друга]
"""
from src.styles.colors import (
    BG_TERTIARY, TEXT_PRIMARY, TEXT_TERTIARY,
    INPUT_BORDER, INPUT_BORDER_FOCUS, ACCENT_PRIMARY
)
from src.styles.tokens import RADIUS_INPUT
from src.styles.fonts import FONT_FAMILY


def get_input_style():
    """Основное поле ввода."""
    return f"""
        QLineEdit, QTextEdit {{
            background-color: {BG_TERTIARY};
            color: {TEXT_PRIMARY};
            border: 1px solid {INPUT_BORDER};
            border-radius: {RADIUS_INPUT}px;
            padding: 12px 16px;
            font-size: 15px;
            font-family: {FONT_FAMILY};
            selection-background-color: {ACCENT_PRIMARY};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {INPUT_BORDER_FOCUS};
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {TEXT_TERTIARY};
        }}
    """