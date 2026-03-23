"""
Настройки и цветовая схема мессенджера Ten Dem
Современный минимализм — дизайн-система v2.0
"""

# ============================================================================
# ЦВЕТОВАЯ СХЕМА (ТЁМНАЯ ТЕМА — ПО УМОЛЧАНИЮ)
# ============================================================================

# 2.1. Фоны
BG_PRIMARY = '#0A0A0A'      # Основной фон приложения
BG_SECONDARY = '#141414'    # Панели, карточки, левая панель
BG_TERTIARY = '#1E1E1E'     # Поля ввода, ховеры, чужие сообщения

# 2.2. Акцент (уникальный фиолетовый)
ACCENT_PRIMARY = '#7C3AED'  # Кнопки, свои сообщения, активные иконки
ACCENT_HOVER = '#8B5CF6'    # Наведение
ACCENT_PRESSED = '#6D28D9'  # Нажатие

# 2.3. Текст
TEXT_PRIMARY = '#FFFFFF'    # Белый
TEXT_SECONDARY = '#A0A0A0'  # Второстепенный
TEXT_TERTIARY = '#6B6B6B'   # Время, метки
TEXT_ON_ACCENT = '#FFFFFF'  # Текст на фиолетовом

# 2.4. Сообщения
MESSAGE_OWN_BG = '#7C3AED'      # Свои сообщения
MESSAGE_OWN_TEXT = '#FFFFFF'
MESSAGE_OTHER_BG = '#1E1E1E'    # Чужие сообщения
MESSAGE_OTHER_TEXT = '#FFFFFF'
MESSAGE_TIME = '#6B6B6B'

# 2.5. Статусы
ONLINE = '#10B981'          # Изумрудный
OFFLINE = '#4B5563'         # Серый
UNREAD_BADGE = '#EF4444'    # Красный
DELIVERED_CHECK = '#6B6B6B' # Серая галочка
READ_CHECK = '#10B981'      # Зелёная галочка

# 2.6. Границы и иконки
DIVIDER = '#2A2A2A'             # Разделители
INPUT_BORDER = '#333333'        # Рамка полей
INPUT_BORDER_FOCUS = '#7C3AED'  # Рамка при фокусе
ICON_DEFAULT = '#9CA3AF'        # Иконки по умолчанию
ICON_HOVER = '#FFFFFF'          # Иконки при наведении
ICON_ACTIVE = '#7C3AED'         # Активные иконки

# 2.7. Системные
SUCCESS = '#10B981'     # Зелёный
ERROR = '#EF4444'       # Красный
WARNING = '#F59E0B'     # Оранжевый

# ============================================================================
# СВЕТЛАЯ ТЕМА
# ============================================================================

LIGHT_THEME = {
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F8F9FA',
    'bg_tertiary': '#E9ECEF',
    'accent_primary': '#7C3AED',
    'accent_hover': '#8B5CF6',
    'accent_pressed': '#6D28D9',
    'text_primary': '#1A1A1A',
    'text_secondary': '#6B7280',
    'text_tertiary': '#9CA3AF',
    'message_own_bg': '#7C3AED',
    'message_own_text': '#FFFFFF',
    'message_other_bg': '#F3F4F6',
    'message_other_text': '#1A1A1A',
    'online': '#10B981',
    'offline': '#9CA3AF',
    'divider': '#E5E7EB',
    'input_border': '#D1D5DB',
    'input_border_focus': '#7C3AED',
}

# ============================================================================
# РАЗМЕРЫ И ОТСТУПЫ
# ============================================================================

# Отступы
PADDING_CARD = 16
PADDING_ELEMENT = 12
PADDING_INPUT = (14, 18)
MARGIN_BETWEEN_ELEMENTS = 8
MARGIN_BETWEEN_SECTIONS = 24

# Скругления
RADIUS_CARD = 16
RADIUS_MESSAGE = 20
RADIUS_BUTTON = 12
RADIUS_INPUT = 24
RADIUS_BADGE = 9999
RADIUS_AVATAR = 50

# Размеры
AVATAR_LIST = 52
AVATAR_CHAT = 40
AVATAR_PROFILE = 80
LEFT_PANEL_WIDTH = 360
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700
ICON_SIZE_SMALL = 20
ICON_SIZE_MEDIUM = 24
ICON_SIZE_LARGE = 32

# ============================================================================
# ШРИФТЫ
# ============================================================================

FONT_FAMILY = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
FONT_SIZE_H1 = 24
FONT_SIZE_H2 = 20
FONT_SIZE_NAME = 16
FONT_SIZE_MESSAGE = 15
FONT_SIZE_SECONDARY = 14
FONT_SIZE_TIME = 12
FONT_SIZE_LABEL = 13

FONT_WEIGHT_BOLD = 700
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_REGULAR = 400

LINE_HEIGHT = 1.4

# ============================================================================
# АНИМАЦИИ
# ============================================================================

ANIMATION_DURATION_FAST = 100     # ms
ANIMATION_DURATION_NORMAL = 200   # ms
ANIMATION_DURATION_SLOW = 300     # ms

SHADOW_LIGHT = '0 4px 12px rgba(0,0,0,0.1)'
SHADOW_MEDIUM = '0 8px 24px rgba(0,0,0,0.15)'
# ============================================================================
# АЛИАСЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ (старые названия цветов)
# ============================================================================

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
FONT_SIZE_NAME = FONT_SIZE_NAME
INPUT_BORDER_RADIUS = RADIUS_INPUT
BUTTON_BORDER_RADIUS = RADIUS_BUTTON

# ============================================================================
# АЛИАСЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ (старые названия)
# ============================================================================

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
FONT_SIZE_NAME = FONT_SIZE_NAME
INPUT_BORDER_RADIUS = RADIUS_INPUT
BUTTON_BORDER_RADIUS = RADIUS_BUTTON

# Аватарки
AVATAR_SIZE_MAIN = AVATAR_LIST      # 52px
AVATAR_SIZE_CHAT = AVATAR_CHAT      # 40px
AVATAR_SIZE_PROFILE = AVATAR_PROFILE # 80px

# ============================================================================
# АЛИАСЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ (ВСЕ СТАРЫЕ НАЗВАНИЯ)
# ============================================================================

# Цвета (основные)
COLOR_BACKGROUND = BG_PRIMARY
COLOR_PANEL = BG_SECONDARY
COLOR_INPUT_BG = BG_TERTIARY
COLOR_TEXT_PRIMARY = TEXT_PRIMARY
COLOR_TEXT_SECONDARY = TEXT_SECONDARY
COLOR_TEXT_TERTIARY = TEXT_TERTIARY
COLOR_DIVIDER = DIVIDER
COLOR_ACCENT = ACCENT_PRIMARY
COLOR_ACCENT_HOVER = ACCENT_HOVER
COLOR_ONLINE = ONLINE
COLOR_OFFLINE = OFFLINE
COLOR_ERROR = ERROR
COLOR_SUCCESS = SUCCESS
COLOR_WARNING = WARNING

# Цвета (ввод)
COLOR_INPUT_BORDER = INPUT_BORDER
COLOR_INPUT_BORDER_FOCUS = INPUT_BORDER_FOCUS

# Цвета (сообщения)
COLOR_MESSAGE_OWN = MESSAGE_OWN_BG
COLOR_MESSAGE_OTHER = MESSAGE_OTHER_BG
COLOR_MESSAGE_TIME = MESSAGE_TIME
COLOR_MESSAGE_OWN_TEXT = MESSAGE_OWN_TEXT
COLOR_MESSAGE_OTHER_TEXT = MESSAGE_OTHER_TEXT

# Цвета (статусы)
COLOR_UNREAD_BADGE = UNREAD_BADGE
COLOR_DELIVERED_CHECK = DELIVERED_CHECK
COLOR_READ_CHECK = READ_CHECK

# Цвета (иконки)
COLOR_ICON_DEFAULT = ICON_DEFAULT
COLOR_ICON_HOVER = ICON_HOVER
COLOR_ICON_ACTIVE = ICON_ACTIVE

# Размеры (аватарки)
AVATAR_SIZE_MAIN = AVATAR_LIST
AVATAR_SIZE_CHAT = AVATAR_CHAT
AVATAR_SIZE_PROFILE = AVATAR_PROFILE

# Размеры (окна)
WINDOW_MIN_WIDTH = WINDOW_MIN_WIDTH
WINDOW_MIN_HEIGHT = WINDOW_MIN_HEIGHT
LEFT_PANEL_WIDTH = LEFT_PANEL_WIDTH

# Размеры (иконки)
ICON_SIZE_SMALL = ICON_SIZE_SMALL
ICON_SIZE_MEDIUM = ICON_SIZE_MEDIUM
ICON_SIZE_LARGE = ICON_SIZE_LARGE

# Скругления
INPUT_BORDER_RADIUS = RADIUS_INPUT
BUTTON_BORDER_RADIUS = RADIUS_BUTTON
RADIUS_CARD = RADIUS_CARD
RADIUS_MESSAGE = RADIUS_MESSAGE
RADIUS_BADGE = RADIUS_BADGE
RADIUS_AVATAR = RADIUS_AVATAR

# Отступы
PADDING_CARD = PADDING_CARD
PADDING_ELEMENT = PADDING_ELEMENT
PADDING_INPUT = PADDING_INPUT
MARGIN_BETWEEN_ELEMENTS = MARGIN_BETWEEN_ELEMENTS
MARGIN_BETWEEN_SECTIONS = MARGIN_BETWEEN_SECTIONS

# Шрифты
FONT_FAMILY = FONT_FAMILY
FONT_SIZE_H1 = FONT_SIZE_H1
FONT_SIZE_H2 = FONT_SIZE_H2
FONT_SIZE_NAME = FONT_SIZE_NAME
FONT_SIZE_MESSAGE = FONT_SIZE_MESSAGE
FONT_SIZE_SECONDARY = FONT_SIZE_SECONDARY
FONT_SIZE_TIME = FONT_SIZE_TIME
FONT_SIZE_LABEL = FONT_SIZE_LABEL

FONT_WEIGHT_BOLD = FONT_WEIGHT_BOLD
FONT_WEIGHT_SEMIBOLD = FONT_WEIGHT_SEMIBOLD
FONT_WEIGHT_MEDIUM = FONT_WEIGHT_MEDIUM
FONT_WEIGHT_REGULAR = FONT_WEIGHT_REGULAR

LINE_HEIGHT = LINE_HEIGHT

# Анимации
ANIMATION_DURATION_FAST = ANIMATION_DURATION_FAST
ANIMATION_DURATION_NORMAL = ANIMATION_DURATION_NORMAL
ANIMATION_DURATION_SLOW = ANIMATION_DURATION_SLOW

SHADOW_LIGHT = SHADOW_LIGHT
SHADOW_MEDIUM = SHADOW_MEDIUM