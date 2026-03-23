"""
Экран загрузки для Ten Dem
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont


class LoadingOverlay(QWidget):
    """Оверлей загрузки на весь экран."""
    
    finished = pyqtSignal()  # Сигнал по завершении загрузки
    
    def __init__(self, parent=None, theme='dark'):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        # Фон зависит от темы
        bg_color = '#0F0F12' if self.theme == 'dark' else '#F5F7FA'
        text_color = '#FFFFFF' if self.theme == 'dark' else '#1A1B1E'
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Спиннер (анимация)
        self.spinner = QLabel("⏳")
        self.spinner.setStyleSheet(f"""
            font-size: 64px;
            color: {text_color};
        """)
        self.spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinner)
        
        # Текст загрузки
        self.label = QLabel("Подготавливаем ваш мессенджер...")
        self.label.setStyleSheet(f"""
            color: {text_color};
            font-size: 18px;
            font-family: Segoe UI, Arial, sans-serif;
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # Прогресс бар
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(300, 6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #25262B;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: #6C5CE7;
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Таймер загрузки (7 секунд)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.elapsed = 0
        self.duration = 7000  # 7 секунд
        self.step = 100  # Обновление каждые 100мс
    
    def start_loading(self):
        """Запускает загрузку."""
        self.elapsed = 0
        self.progress.setValue(0)
        self.timer.start(self.step)
    
    def update_progress(self):
        """Обновляет прогресс."""
        self.elapsed += self.step
        progress = min(100, int((self.elapsed / self.duration) * 100))
        self.progress.setValue(progress)
        
        if self.elapsed >= self.duration:
            self.timer.stop()
            self.finished.emit()
    
    def stop_loading(self):
        """Останавливает загрузку."""
        self.timer.stop()
        