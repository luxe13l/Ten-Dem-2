"""Legal agreement screen."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


DOCS = {
    "terms": ("Пользовательское соглашение", "terms.txt"),
    "privacy": ("Политика конфиденциальности", "privacy.txt"),
    "consent": ("Согласие на обработку данных", "consent.txt"),
    "transfer": ("Согласие на передачу в Firebase", "transfer.txt"),
}


class AgreementRow(QWidget):
    stateChanged = pyqtSignal()
    openRequested = pyqtSignal(str)

    def __init__(self, label: str, doc_key: str | None = None, parent=None):
        super().__init__(parent)
        self.doc_key = doc_key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(lambda _: self.stateChanged.emit())
        self.checkbox.setStyleSheet(
            """
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 1px solid #3A3A45;
                background-color: #18181D;
            }
            QCheckBox::indicator:checked {
                background-color: #10B981;
                border: 1px solid #10B981;
            }
            """
        )
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        title = QLabel(label)
        title.setWordWrap(True)
        title.setStyleSheet("color: white; font-size: 15px; font-weight: 500;")
        text_layout.addWidget(title)
        if doc_key:
            open_btn = QPushButton("Открыть документ")
            open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            open_btn.clicked.connect(lambda: self.openRequested.emit(doc_key))
            open_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    color: #8B5CF6;
                    border: none;
                    text-align: left;
                    padding: 0;
                    font-size: 13px;
                }
                """
            )
            text_layout.addWidget(open_btn, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(text_layout, 1)

    def isChecked(self):
        return self.checkbox.isChecked()


class LegalAgreementWindow(QWidget):
    completed = pyqtSignal(bool)

    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.rows = []
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #0E0E12;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        root.addWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setStyleSheet(
            """
            QFrame {
                background-color: #15151B;
                border: 1px solid #23232D;
                border-radius: 24px;
            }
            """
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Юридические документы")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: 700;")
        hero_layout.addWidget(title)
        subtitle = QLabel(
            f"Почти готово, {self.user_data.get('name', 'пользователь')}. "
            "Чтобы завершить регистрацию, подтвердите согласие с документами."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 14px; line-height: 1.5;")
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        for label, doc_key in [
            ("Я принимаю пользовательское соглашение", "terms"),
            ("Я согласен с политикой конфиденциальности", "privacy"),
            ("Я даю согласие на обработку персональных данных", "consent"),
            ("Я согласен на передачу данных в Firebase", "transfer"),
            ("Мне уже исполнилось 14 лет", None),
        ]:
            row = AgreementRow(label, doc_key)
            row.stateChanged.connect(self.update_state)
            row.openRequested.connect(self.open_document)
            self.rows.append(row)
            layout.addWidget(row)

        note = QLabel("Документы открываются внутри приложения. Перед созданием аккаунта все пункты должны быть подтверждены.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #71717A; font-size: 12px;")
        layout.addWidget(note)

        self.continue_btn = QPushButton("Завершить регистрацию")
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.finish)
        self.continue_btn.setMinimumHeight(54)
        self.continue_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                font-weight: 700;
            }
            QPushButton:disabled {
                background-color: #252530;
                color: #71717A;
            }
            QPushButton:hover:!disabled {
                background-color: #059669;
            }
            """
        )
        layout.addWidget(self.continue_btn)
        layout.addStretch()
        scroll.setWidget(container)

    def update_state(self):
        self.continue_btn.setEnabled(all(row.isChecked() for row in self.rows))

    def open_document(self, doc_key: str):
        title, file_name = DOCS[doc_key]
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(760, 620)
        dialog.setStyleSheet("background-color: #101015; color: white;")
        layout = QVBoxLayout(dialog)

        heading = QLabel(title)
        heading.setStyleSheet("color: white; font-size: 20px; font-weight: 700;")
        layout.addWidget(heading)

        browser = QTextBrowser()
        browser.setStyleSheet(
            """
            QTextBrowser {
                background-color: #17171D;
                border: 1px solid #2A2A34;
                border-radius: 16px;
                padding: 18px;
                color: white;
                font-size: 14px;
            }
            """
        )
        doc_path = Path(__file__).resolve().parents[2] / "assets" / "docs" / file_name
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            text = text.replace("[ИМЯ]", self.user_data.get("name", "Пользователь"))
        else:
            text = f"Документ {file_name} пока не найден."
        browser.setText(text)
        layout.addWidget(browser, 1)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #23232B;
                color: white;
                border: 1px solid #32323C;
                border-radius: 14px;
            }
            """
        )
        layout.addWidget(close_btn)
        dialog.exec()

    def finish(self):
        if self.continue_btn.isEnabled():
            self.completed.emit(True)
