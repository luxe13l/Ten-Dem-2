"""
Виджет выбора темы оформления для Ten Dem
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from src.utils.theme_manager import theme_manager


class ThemeCard(QWidget):
    """Карточка темы для выбора."""
    
    selected = pyqtSignal(str)  # Сигнал при выборе темы
    
    def __init__(self, theme_name, icon, title, preview_color, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.is_selected = False
        
        self.init_ui(icon, title, preview_color)
    
    def init_ui(self, icon, title, preview_color):
        """Инициализация интерфейса."""
        self.setFixedSize(300, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Фон карточки
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {preview_color};
                border-radius: 32px;
                border: 4px solid transparent;
            }}
            QWidget:hover {{
                background-color: {preview_color};
            }}
        """)
        
        # Иконка
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Название
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            font-family: Segoe UI, Arial, sans-serif;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Превью элементов
        preview_widget = QWidget()
        preview_widget.setFixedSize(200, 100)
        preview_widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255,255,255,0.2);
                border-radius: 16px;
            }}
        """)
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        
        # Пузырёк сообщения
        bubble = QLabel("Сообщение")
        bubble.setStyleSheet("""
            background-color: rgba(255,255,255,0.3);
            color: white;
            border-radius: 12px;
            padding: 8px;
            font-size: 12px;
        """)
        preview_layout.addWidget(bubble)
        
        layout.addWidget(preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """Обработка клика."""
        self.select()
        super().mousePressEvent(event)
    
    def select(self):
        """Выбирает эту тему."""
        self.is_selected = True
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style().palette().color(0).name()};
                border-radius: 32px;
                border: 4px solid #6C5CE7;
            }}
        """)
        self.selected.emit(self.theme_name)
    
    def deselect(self):
        """Снимает выбор."""
        self.is_selected = False
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style().palette().color(0).name()};
                border-radius: 32px;
                border: 4px solid transparent;
            }}
        """)


class ThemeSelector(QWidget):
    """Виджет выбора темы оформления."""
    
    theme_chosen = pyqtSignal(str)  # Сигнал с выбранной темой
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_theme = 'dark'
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)
        
        # Заголовок
        title = QLabel("Выберите оформление")
        title.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
            font-family: Segoe UI, Arial, sans-serif;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Подзаголовок
        subtitle = QLabel("Тему можно будет изменить в настройках")
        subtitle.setStyleSheet("""
            color: #9A9CA5;
            font-size: 14px;
            font-family: Segoe UI, Arial, sans-serif;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Карточки тем
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Тёмная тема
        self.dark_card = ThemeCard(
            theme_name='dark',
            icon='🌙',
            title='Тёмная',
            preview_color='#1A1B1E'
        )
        self.dark_card.selected.connect(self.on_theme_selected)
        cards_layout.addWidget(self.dark_card)
        
        # Светлая тема
        self.light_card = ThemeCard(
            theme_name='light',
            icon='☀️',
            title='Светлая',
            preview_color='#F5F7FA'
        )
        self.light_card.selected.connect(self.on_theme_selected)
        cards_layout.addWidget(self.light_card)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        # По умолчанию выбрана тёмная
        self.dark_card.select()
    
    def on_theme_selected(self, theme_name):
        """Обработка выбора темы."""
        self.selected_theme = theme_name
        
        # Снимаем выбор с другой карточки
        if theme_name == 'dark':
            self.light_card.deselect()
        else:
            self.dark_card.deselect()
    
    def get_selected_theme(self):
        """Получает выбранную тему."""
        return self.selected_theme