import sys
from PyQt6.QtWidgets import QApplication
from src.models.user import User
from src.ui.main_window import MainWindow

app = QApplication(sys.argv)

user = User(uid='test', phone='+79999999999', name='Тест')
window = MainWindow(user)

print("🟢 Показ окна...")
window.show()
window.raise_()
window.activateWindow()

print(f"✅ Окно видно: {window.isVisible()}")
print(f"✅ Размер: {window.size()}")

# ✅ Загружаем контакты ПОСЛЕ показа окна
print("🟢 Загрузка контактов...")
window.load_contacts()

sys.exit(app.exec())