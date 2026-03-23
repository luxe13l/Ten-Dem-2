"""
Менеджер тем оформления для Ten Dem
"""
from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.settings import LIGHT_THEME


class ThemeManager(QObject):
    """Управление темами приложения."""
    
    theme_changed = pyqtSignal(str)  # Сигнал при смене темы
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'
        self.colors = self._get_dark_theme()
    
    def _get_dark_theme(self):
        """Возвращает цвета тёмной темы."""
        from src.utils.settings import (
            BG_PRIMARY, BG_SECONDARY, BG_TERTIARY,
            ACCENT_PRIMARY, ACCENT_HOVER, ACCENT_PRESSED,
            TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
            MESSAGE_OWN_BG, MESSAGE_OTHER_BG,
            ONLINE, OFFLINE, DIVIDER, INPUT_BORDER, INPUT_BORDER_FOCUS,
            ICON_DEFAULT, ICON_HOVER, ICON_ACTIVE,
            SUCCESS, ERROR, WARNING, READ_CHECK, DELIVERED_CHECK
        )
        
        return {
            'bg_primary': BG_PRIMARY,
            'bg_secondary': BG_SECONDARY,
            'bg_tertiary': BG_TERTIARY,
            'accent_primary': ACCENT_PRIMARY,
            'accent_hover': ACCENT_HOVER,
            'accent_pressed': ACCENT_PRESSED,
            'text_primary': TEXT_PRIMARY,
            'text_secondary': TEXT_SECONDARY,
            'text_tertiary': TEXT_TERTIARY,
            'message_own_bg': MESSAGE_OWN_BG,
            'message_other_bg': MESSAGE_OTHER_BG,
            'online': ONLINE,
            'offline': OFFLINE,
            'divider': DIVIDER,
            'input_border': INPUT_BORDER,
            'input_border_focus': INPUT_BORDER_FOCUS,
            'icon_default': ICON_DEFAULT,
            'icon_hover': ICON_HOVER,
            'icon_active': ICON_ACTIVE,
            'success': SUCCESS,
            'error': ERROR,
            'warning': WARNING,
            'read_check': READ_CHECK,
            'delivered_check': DELIVERED_CHECK,
        }
    
    def set_theme(self, theme_name: str):
        """Устанавливает тему."""
        if theme_name == 'light':
            self.current_theme = 'light'
            self.colors = LIGHT_THEME.copy()
        else:
            self.current_theme = 'dark'
            self.colors = self._get_dark_theme()
        
        self.theme_changed.emit(self.current_theme)
    
    def get_color(self, name: str) -> str:
        """Получает цвет по имени."""
        return self.colors.get(name, '#000000')
    
    def is_dark(self) -> bool:
        """Проверяет, тёмная ли тема."""
        return self.current_theme == 'dark'


# Глобальный экземпляр
theme_manager = ThemeManager()