import sys
from PyQt6.QtWidgets import QApplication
from src.ui.legal_agreement import LegalAgreementWindow

app = QApplication(sys.argv)

user_data = {
    'name': 'Лев',
    'phone': '+79999999999',
    'username': 'test'
}

window = LegalAgreementWindow(user_data)
window.show()

sys.exit(app.exec())