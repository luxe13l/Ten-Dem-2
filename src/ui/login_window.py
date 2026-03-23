import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.database.users_db import get_user_by_phone, create_user
from src.models.user import User
from src.utils.settings import (
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ERROR, COLOR_ACCENT,
    COLOR_PANEL, COLOR_INPUT_BG, COLOR_INPUT_BORDER,
    BUTTON_BORDER_RADIUS, INPUT_BORDER_RADIUS, FONT_FAMILY
)


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.verification_id = None
        self.timer = QTimer()
        self.seconds_left = 0
        self.init_ui()
        
    def init_ui(self):
        try:
            self.setWindowTitle("Вход — Ten Dem")
            self.setMinimumSize(400, 450)
            self.setModal(True)  # ✅ МОДАЛЬНОЕ
            
            # Центрирование
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 400) // 2
            y = (screen.height() - 450) // 2
            self.move(x, y)
            
            layout = QVBoxLayout()
            layout.setSpacing(20)
            layout.setContentsMargins(40, 40, 40, 40)
            
            title = QLabel("Ten Dem")
            title.setFont(QFont(FONT_FAMILY, 24, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
            layout.addWidget(title)
            
            subtitle = QLabel("Войдите, чтобы продолжить")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px;")
            layout.addWidget(subtitle)
            
            layout.addSpacing(20)
            
            self.phone_input = QLineEdit()
            self.phone_input.setPlaceholderText("+7 (999) 999-99-99")
            self.phone_input.textChanged.connect(self.format_phone_input)
            self.phone_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLOR_INPUT_BG};
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_INPUT_BORDER};
                    border-radius: {INPUT_BORDER_RADIUS}px;
                    padding: 12px 16px;
                    font-size: 15px;
                    font-family: {FONT_FAMILY};
                }}
            """)
            layout.addWidget(self.phone_input)
            
            self.code_btn = QPushButton("Получить код")
            self.code_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: white;
                    border: none;
                    border-radius: {BUTTON_BORDER_RADIUS}px;
                    padding: 12px;
                    font-size: 15px;
                    font-family: {FONT_FAMILY};
                    font-weight: bold;
                }}
            """)
            self.code_btn.clicked.connect(self.send_code)
            layout.addWidget(self.code_btn)
            
            self.code_input = QLineEdit()
            self.code_input.setPlaceholderText("Введите код из СМС")
            self.code_input.setVisible(False)
            self.code_input.setMaxLength(6)
            self.code_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLOR_INPUT_BG};
                    color: {COLOR_TEXT_PRIMARY};
                    border: 1px solid {COLOR_INPUT_BORDER};
                    border-radius: {INPUT_BORDER_RADIUS}px;
                    padding: 12px 16px;
                    font-size: 15px;
                    font-family: {FONT_FAMILY};
                }}
            """)
            layout.addWidget(self.code_input)
            
            self.login_btn = QPushButton("Войти")
            self.login_btn.setVisible(False)
            self.login_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: white;
                    border: none;
                    border-radius: {BUTTON_BORDER_RADIUS}px;
                    padding: 12px;
                    font-size: 15px;
                    font-family: {FONT_FAMILY};
                    font-weight: bold;
                }}
            """)
            self.login_btn.clicked.connect(self.verify_code)
            layout.addWidget(self.login_btn)
            
            self.skip_btn = QPushButton("Пропустить (тест)")
            self.skip_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOR_TEXT_SECONDARY};
                    border: 1px solid {COLOR_INPUT_BORDER};
                    border-radius: {BUTTON_BORDER_RADIUS}px;
                    padding: 10px;
                    font-size: 14px;
                    font-family: {FONT_FAMILY};
                }}
            """)
            self.skip_btn.clicked.connect(self.skip_login)
            layout.addWidget(self.skip_btn)
            
            self.error_label = QLabel()
            self.error_label.setStyleSheet(f"color: {COLOR_ERROR}; font-size: 13px;")
            self.error_label.setWordWrap(True)
            layout.addWidget(self.error_label)
            
            self.setLayout(layout)
            
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.update_timer)
            
        except Exception as e:
            print(f"Ошибка init_ui: {e}")
            import traceback
            traceback.print_exc()
    
    def format_phone_input(self, text):
        try:
            digits = re.sub(r'\D', '', text)
            if digits.startswith('8'):
                digits = '7' + digits[1:]
            if not digits.startswith('7'):
                digits = '7' + digits
            digits = digits[:11]
            
            if len(digits) <= 1:
                formatted = f"+{digits}"
            elif len(digits) <= 4:
                formatted = f"+7 ({digits[1:]}"
            elif len(digits) <= 7:
                formatted = f"+7 ({digits[1:4]}) {digits[4:]}"
            elif len(digits) <= 9:
                formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                formatted = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
            
            if self.phone_input.text() != formatted:
                self.phone_input.setText(formatted)
                self.phone_input.setCursorPosition(len(formatted))
        except Exception:
            pass
    
    def send_code(self):
        try:
            phone = re.sub(r'\D', '', self.phone_input.text())
            if len(phone) != 11:
                self.error_label.setText("Введите корректный номер")
                return
            
            self.error_label.clear()
            self.verification_id = "test_mode"
            
            self.code_input.setVisible(True)
            self.login_btn.setVisible(True)
            self.code_btn.setEnabled(False)
            self.code_btn.setText("Отправить код повторно (60с)")
            
            self.seconds_left = 60
            self.timer.start()
        except Exception as e:
            self.error_label.setText(f"Ошибка: {e}")
    
    def update_timer(self):
        try:
            self.seconds_left -= 1
            if self.seconds_left > 0:
                self.code_btn.setText(f"Отправить код повторно ({self.seconds_left}с)")
            else:
                self.timer.stop()
                self.code_btn.setEnabled(True)
                self.code_btn.setText("Получить код")
        except Exception:
            pass
    
    def verify_code(self):
        try:
            code = self.code_input.text().strip()
            if len(code) != 6:
                self.error_label.setText("Код должен содержать 6 цифр")
                return
            
            phone = re.sub(r'\D', '', self.phone_input.text())
            
            # ✅ ПРАВИЛЬНО: user_data (полное имя)
            user_data = get_user_by_phone(phone)
            
            if user_data:  # ✅ ПРАВИЛЬНО: user_data, НЕ user_
                self.current_user = User.from_dict(user_data, user_data['uid'])
                print(f"Пользователь найден: {self.current_user.name}")
            else:
                from datetime import datetime
                new_uid = create_user({
                    'phone': phone,
                    'name': f"Пользователь {phone[-4:]}",
                    'avatar_url': '',
                    'status': 'online',
                    'last_seen': datetime.now()
                })
                if new_uid:
                    self.current_user = User(
                        uid=new_uid, phone=phone, 
                        name=f"Пользователь {phone[-4:]}",
                        status='online'
                    )
                    print(f"Пользователь создан: {self.current_user.name}")
            
            if self.current_user:
                print("✅ Вход успешен, закрываем с кодом 1")
                self.accept()  # ✅ Возвращает 1
            else:
                self.error_label.setText("Ошибка входа")
        except Exception as e:
            print(f"Ошибка verify_code: {e}")
            self.error_label.setText(f"Ошибка: {e}")
    
    def skip_login(self):
        try:
            from datetime import datetime
            self.current_user = User(
                uid="test_user_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                phone="+79990000000",
                name="Тестовый пользователь",
                status="online",
                last_seen=datetime.now()
            )
            print(f"✅ Тестовый пользователь: {self.current_user.name}")
            print("✅ Закрываем окно с кодом 1")
            self.accept()  # ✅ ВОЗВРАЩАЕТ 1 (не done(1), не reject())
        except Exception as e:
            print(f"Ошибка skip_login: {e}")
            self.error_label.setText(f"Ошибка: {e}")
    
    def get_user(self):
        return self.current_user