# test_qt.py
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
import sys

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Тест PyQt6")
window.setMinimumSize(400, 300)
label = QLabel("Если ты это видишь — PyQt6 работает!", window)
label.setStyleSheet("font-size: 20px; color: green;")
window.show()
print("Окно показано!")
sys.exit(app.exec())
