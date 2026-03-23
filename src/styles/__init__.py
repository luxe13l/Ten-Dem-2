"""
Система стилей Ten Dem
Отвечает: [Имя друга]
Импорт всех стилей в одном месте.
"""

# Цвета
from src.styles.colors import *

# Шрифты
from src.styles.fonts import *

# Токены (размеры, отступы)
from src.styles.tokens import *

# Темы
from src.styles.themes import theme_manager

# Компоненты
from src.styles.components import *

# ============================================================================
# ОБРАТНАЯ СОВМЕСТИМОСТЬ (старые названия)
# ============================================================================

# Для старых файлов которые ещё не обновили
COLOR_BACKGROUND = BG_PRIMARY
COLOR_PANEL = BG_SECONDARY
COLOR_INPUT_BG = BG_TERTIARY
COLOR_TEXT_PRIMARY = TEXT_PRIMARY
COLOR_TEXT_SECONDARY = TEXT_SECONDARY
COLOR_DIVIDER = DIVIDER
COLOR_ACCENT = ACCENT_PRIMARY
COLOR_ACCENT_HOVER = ACCENT_HOVER
COLOR_ONLINE = ONLINE
COLOR_ERROR = ERROR
COLOR_INPUT_BORDER = INPUT_BORDER
COLOR_INPUT_BORDER_FOCUS = INPUT_BORDER_FOCUS
COLOR_MESSAGE_OWN = MESSAGE_OWN_BG
COLOR_MESSAGE_OTHER = MESSAGE_OTHER_BG
INPUT_BORDER_RADIUS = RADIUS_INPUT
BUTTON_BORDER_RADIUS = RADIUS_BUTTON