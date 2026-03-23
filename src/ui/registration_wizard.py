"""Registration wizard with real validation."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.database.auth_manager import auth_manager
from src.database.users_db import get_user_by_phone
from src.ui.legal_agreement import LegalAgreementWindow


PROFANITY_PARTS = ("хуй", "хуе", "еб", "пизд", "бля", "сук", "fuck", "shit")


def contains_profanity(value: str) -> bool:
    lowered = (value or "").lower()
    return any(part in lowered for part in PROFANITY_PARTS)


def primary_button_style() -> str:
    return """
    QPushButton {
        background-color: #10B981;
        color: white;
        border: none;
        border-radius: 16px;
        font-size: 15px;
        font-weight: 600;
        text-align: center;
        padding: 12px;
    }
    QPushButton:hover:!disabled { background-color: #059669; }
    QPushButton:disabled { background-color: rgba(16,185,129,0.35); color: rgba(255,255,255,0.75); }
    """


def secondary_button_style() -> str:
    return """
    QPushButton {
        background-color: #23232B;
        color: white;
        border: 1px solid #31313A;
        border-radius: 16px;
        font-size: 15px;
        font-weight: 600;
        text-align: center;
        padding: 12px;
    }
    QPushButton:hover:!disabled { background-color: #2A2A34; }
    QPushButton:disabled { background-color: rgba(35,35,43,0.45); color: rgba(255,255,255,0.55); }
    """


def input_style() -> str:
    return """
    QLineEdit {
        background-color: #17171D;
        color: white;
        border: 1px solid #2F2F38;
        border-radius: 16px;
        padding: 16px 18px;
        font-size: 16px;
    }
    """


class PhoneStep(QWidget):
    next_step = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(72, 90, 72, 72)
        layout.setSpacing(18)

        title = QLabel("Ten Dem")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 34px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Введите номер телефона")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #9CA3AF; font-size: 15px;")
        layout.addWidget(subtitle)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7 (999) 999-99-99")
        self.phone_input.setStyleSheet(input_style())
        self.phone_input.textChanged.connect(self.format_phone)
        self.phone_input.textChanged.connect(self.update_buttons)
        layout.addWidget(self.phone_input)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        self.register_btn = QPushButton("Создать аккаунт")
        self.register_btn.setStyleSheet(primary_button_style())
        self.register_btn.setEnabled(False)
        self.register_btn.clicked.connect(lambda: self.submit(False))
        layout.addWidget(self.register_btn)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setStyleSheet(secondary_button_style())
        self.login_btn.setEnabled(False)
        self.login_btn.clicked.connect(lambda: self.submit(True))
        layout.addWidget(self.login_btn)

        skip_btn = QPushButton("Тестовый вход")
        skip_btn.setStyleSheet("background: transparent; color: #9CA3AF; border: none; padding: 10px;")
        skip_btn.clicked.connect(lambda: self.next_step.emit("skip", False))
        layout.addWidget(skip_btn)
        layout.addStretch()

    def format_phone(self, text: str):
        digits = "".join(c for c in text if c.isdigit())
        if digits.startswith("8"):
            digits = "7" + digits[1:]
        if digits and not digits.startswith("7"):
            digits = "7" + digits
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

    def update_buttons(self):
        is_valid = len("".join(c for c in self.phone_input.text() if c.isdigit())) == 11
        self.register_btn.setEnabled(is_valid)
        self.login_btn.setEnabled(is_valid)

    def submit(self, is_login: bool):
        phone = "".join(c for c in self.phone_input.text() if c.isdigit())
        if len(phone) != 11:
            self.error_label.setText("Введите корректный номер")
            return
        self.error_label.clear()
        self.next_step.emit(phone, is_login)


class CodeStep(QWidget):
    verified = pyqtSignal()
    back_step = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.verification_id = ""
        self.phone = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(72, 90, 72, 72)
        layout.setSpacing(18)

        title = QLabel("Подтверждение номера")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        self.subtitle = QLabel("")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        layout.addWidget(self.subtitle)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("6 цифр из SMS")
        self.code_input.setStyleSheet(input_style())
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.code_input)

        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        layout.addWidget(self.timer_label)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        self.continue_btn = QPushButton("Подтвердить")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(primary_button_style())
        self.continue_btn.clicked.connect(self.submit)
        layout.addWidget(self.continue_btn)

        back_btn = QPushButton("Назад")
        back_btn.setStyleSheet(secondary_button_style())
        back_btn.clicked.connect(self.back_step.emit)
        layout.addWidget(back_btn)
        layout.addStretch()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.seconds_left = 60

    def setup(self, phone: str, verification_id: str):
        self.phone = phone
        self.verification_id = verification_id
        self.subtitle.setText(f"Код отправлен на +{phone}")
        self.code_input.clear()
        self.error_label.clear()
        self.seconds_left = 60
        self.timer.start(1000)
        self.update_timer()

    def update_timer(self):
        self.seconds_left -= 1
        if self.seconds_left > 0:
            self.timer_label.setText(f"Повторная отправка через {self.seconds_left} сек")
        else:
            self.timer.stop()
            self.timer_label.setText("Можно запросить код снова")

    def on_text_changed(self, text: str):
        self.continue_btn.setEnabled(len(text.strip()) == 6 and text.strip().isdigit())

    def submit(self):
        success, message, _phone = auth_manager.verify_code(self.verification_id, self.code_input.text().strip())
        if success:
            self.verified.emit()
        else:
            self.error_label.setText(message)


class NameStep(QWidget):
    next_step = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(72, 90, 72, 72)
        layout.setSpacing(18)

        title = QLabel("Как вас зовут?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        self.name_input.setStyleSheet(input_style())
        self.name_input.textChanged.connect(self.validate)
        layout.addWidget(self.name_input)

        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Фамилия")
        self.surname_input.setStyleSheet(input_style())
        self.surname_input.textChanged.connect(self.validate)
        layout.addWidget(self.surname_input)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        self.continue_btn = QPushButton("Продолжить")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(primary_button_style())
        self.continue_btn.clicked.connect(self.submit)
        layout.addWidget(self.continue_btn)
        layout.addStretch()

    def validate(self):
        name = self.name_input.text().strip()
        surname = self.surname_input.text().strip()
        valid = bool(re.fullmatch(r"[A-Za-zА-Яа-яЁё]{2,20}", name)) and bool(
            re.fullmatch(r"[A-Za-zА-Яа-яЁё]{2,20}", surname)
        )
        valid = valid and not contains_profanity(name) and not contains_profanity(surname)
        self.continue_btn.setEnabled(valid)

    def submit(self):
        name = self.name_input.text().strip()
        surname = self.surname_input.text().strip()
        if not re.fullmatch(r"[A-Za-zА-Яа-яЁё]{2,20}", name):
            self.error_label.setText("Имя должно содержать только буквы")
            return
        if not re.fullmatch(r"[A-Za-zА-Яа-яЁё]{2,20}", surname):
            self.error_label.setText("Фамилия должна содержать только буквы")
            return
        if contains_profanity(name) or contains_profanity(surname):
            self.error_label.setText("Используйте нормальное имя без ругательств")
            return
        self.error_label.clear()
        self.next_step.emit({"name": name, "surname": surname})


class UsernameStep(QWidget):
    next_step = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.username_timer = QTimer()
        self.username_timer.setSingleShot(True)
        self.username_timer.timeout.connect(self.check_username)
        self.is_username_available = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(72, 90, 72, 72)
        layout.setSpacing(18)

        title = QLabel("Выберите username")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Только латинские буквы и подчёркивание, без цифр")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #9CA3AF; font-size: 13px;")
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("например levas")
        self.username_input.setStyleSheet(input_style())
        self.username_input.textChanged.connect(self.on_username_changed)
        layout.addWidget(self.username_input)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        layout.addWidget(self.error_label)

        self.continue_btn = QPushButton("Продолжить")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(primary_button_style())
        self.continue_btn.clicked.connect(self.submit)
        layout.addWidget(self.continue_btn)
        layout.addStretch()

    def on_username_changed(self, text: str):
        self.username_timer.stop()
        self.is_username_available = False
        self.continue_btn.setEnabled(False)
        self.status_label.clear()
        self.error_label.clear()
        if not text.strip():
            return
        valid, result = auth_manager.validate_username(text)
        if not valid:
            self.error_label.setText(result)
            return
        if contains_profanity(text):
            self.error_label.setText("Username содержит недопустимые слова")
            return
        self.status_label.setText("Проверяем username...")
        self.status_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        self.username_timer.start(350)

    def check_username(self):
        try:
            available, result = auth_manager.check_username_available(self.username_input.text().strip())
            if available:
                self.is_username_available = True
                self.status_label.setText(f"@{result} доступен")
                self.status_label.setStyleSheet("color: #10B981; font-size: 12px;")
                self.continue_btn.setEnabled(True)
            else:
                self.error_label.setText(result)
                self.status_label.clear()
                self.continue_btn.setEnabled(False)
        except Exception as exc:
            self.is_username_available = False
            self.continue_btn.setEnabled(False)
            self.status_label.clear()
            self.error_label.setText("Не удалось проверить username")
            print(f"Ошибка шага username: {exc}")

    def submit(self):
        if not self.is_username_available:
            self.error_label.setText("Сначала дождитесь успешной проверки")
            return
        self.next_step.emit(auth_manager.normalize_username(self.username_input.text().strip()))


class LoadingStep(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Создаём аккаунт")
        label.setStyleSheet("color: white; font-size: 22px; font-weight: 700;")
        layout.addWidget(label)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(280)
        self.progress.setStyleSheet(
            """
            QProgressBar { background-color: #1D1D24; border: none; border-radius: 4px; }
            QProgressBar::chunk { background-color: #10B981; border-radius: 4px; }
            """
        )
        layout.addWidget(self.progress)
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.value = 0

    def start_loading(self):
        self.value = 0
        self.progress.setValue(0)
        self.timer.start(40)

    def tick(self):
        self.value += 2
        self.progress.setValue(self.value)
        if self.value >= 100:
            self.timer.stop()
            self.finished.emit()


class RegistrationWizard(QWidget):
    registration_complete = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ten Dem")
        self.setMinimumSize(500, 700)
        self.resize(500, 700)
        self.setStyleSheet("background-color: #0E0E12;")
        self.phone = ""
        self.user_data = {}
        self.is_login_mode = False
        self.legal_step = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.phone_step = PhoneStep()
        self.code_step = CodeStep()
        self.name_step = NameStep()
        self.username_step = UsernameStep()
        self.loading_step = LoadingStep()

        self.stack.addWidget(self.phone_step)
        self.stack.addWidget(self.code_step)
        self.stack.addWidget(self.name_step)
        self.stack.addWidget(self.username_step)
        self.stack.addWidget(self.loading_step)

        self.phone_step.next_step.connect(self.on_phone_submitted)
        self.code_step.verified.connect(self.on_code_verified)
        self.code_step.back_step.connect(lambda: self.stack.setCurrentWidget(self.phone_step))
        self.name_step.next_step.connect(self.on_name_submitted)
        self.username_step.next_step.connect(self.on_username_submitted)
        self.loading_step.finished.connect(self.on_loading_finished)

    def on_phone_submitted(self, phone: str, is_login: bool):
        if phone == "skip":
            self.registration_complete.emit(
                {"uid": "test_user", "phone": "+79990000000", "name": "Тестовый", "username": "testuser"}
            )
            return
        self.phone = phone
        self.is_login_mode = is_login
        success, message, verification_id = auth_manager.send_verification_code(phone)
        if not success:
            self.phone_step.error_label.setText(message)
            return
        self.code_step.setup(phone, verification_id)
        self.stack.setCurrentWidget(self.code_step)

    def on_code_verified(self):
        if self.is_login_mode:
            user_data = get_user_by_phone(self.phone)
            if not user_data:
                self.code_step.error_label.setText("Аккаунт с этим номером не найден")
                return
            self.registration_complete.emit(
                {
                    "uid": user_data["uid"],
                    "phone": user_data.get("phone", ""),
                    "name": user_data.get("name", ""),
                    "username": user_data.get("username", ""),
                }
            )
            return
        self.stack.setCurrentWidget(self.name_step)

    def on_name_submitted(self, data: dict):
        self.user_data.update(data)
        self.stack.setCurrentWidget(self.username_step)

    def on_username_submitted(self, username: str):
        self.user_data["username"] = username
        self.legal_step = LegalAgreementWindow(self.user_data)
        self.legal_step.completed.connect(self.on_legal_completed)
        if self.stack.indexOf(self.legal_step) == -1:
            self.stack.addWidget(self.legal_step)
        self.stack.setCurrentWidget(self.legal_step)

    def on_legal_completed(self):
        self.stack.setCurrentWidget(self.loading_step)
        self.loading_step.start_loading()

    def on_loading_finished(self):
        success, user_id, message = auth_manager.create_user_profile(
            phone=self.phone,
            name=self.user_data.get("name", ""),
            surname=self.user_data.get("surname", ""),
            username=self.user_data.get("username", ""),
        )
        if not success:
            self.stack.setCurrentWidget(self.username_step)
            self.username_step.error_label.setText(message)
            return
        self.registration_complete.emit(
            {
                "uid": user_id,
                "phone": self.phone,
                "name": self.user_data.get("name", ""),
                "surname": self.user_data.get("surname", ""),
                "username": self.user_data.get("username", ""),
            }
        )
