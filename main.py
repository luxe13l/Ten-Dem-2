"""
Точка входа в мессенджер Ten Dem
"""
import sys
import os
import uuid
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from src.database.firebase_client import init_firebase
from src.database.yandex_storage import init_yandex_storage
from src.database.local_store import load_store
from src.database.users_db import update_user
from src.styles.themes import apply_theme
from src.ui.registration_wizard import RegistrationWizard
from src.ui.main_window import MainWindow


main_window_ref = None
APP_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Логотип Ten Dem.png")


def main():
    print("=== ЗАПУСК TEN DEM ===")
    
    try:
        print("1. Инициализация Firebase...")
        init_firebase()
        
        print("2. Инициализация Яндекс.Хранилища...")
        init_yandex_storage(
            access_key=os.getenv('YANDEX_ACCESS_KEY'),
            secret_key=os.getenv('YANDEX_SECRET_KEY'),
            bucket_name=os.getenv('YANDEX_BUCKET_NAME')
        )
        
        print("3. Создание QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("Ten Dem")
        if os.path.exists(APP_ICON_PATH):
            app.setWindowIcon(QIcon(APP_ICON_PATH))
        app.setStyle("Fusion")
        apply_theme(app, "dark")
        
        print("4. Создание окна регистрации...")
        wizard = RegistrationWizard()
        if os.path.exists(APP_ICON_PATH):
            wizard.setWindowIcon(QIcon(APP_ICON_PATH))
        wizard.registration_complete.connect(lambda data: on_registration_complete(data, wizard, app))
        
        print("5. Показ окна регистрации...")
        wizard.show()
        
        print("6. Запуск...")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter...")
        sys.exit(1)


def on_registration_complete(data, wizard, app):
    """Обработка завершения регистрации/входа"""
    global main_window_ref
    
    print(f"✅ Регистрация завершена: {data}")
    
    wizard.close()
    wizard.deleteLater()
    
    from src.models.user import User
    current_user = User(
        uid=data.get('uid', '') or f"local-{uuid.uuid4().hex[:8]}",
        phone=data.get('phone', ''),
        name=data.get('name', '') or 'Пользователь',
        username=data.get('username', ''),
        surname=data.get('surname', ''),
        bio=data.get('bio', ''),
    )

    user_settings = load_store().get("settings", {}).get(current_user.uid, {})
    current_user.theme = user_settings.get("theme", "dark")
    current_user.username = user_settings.get("username", current_user.username)
    current_user.bio = user_settings.get("bio", current_user.bio)
    apply_theme(app, current_user.theme)

    if current_user.uid:
        update_user(
            current_user.uid,
            {
                'uid': current_user.uid,
                'phone': current_user.phone,
                'name': current_user.name,
                'username': current_user.username,
                'bio': current_user.bio,
                'theme': current_user.theme,
                'status': 'online',
            }
        )
    
    print("7. Создание главного окна мессенджера...")
    main_window_ref = MainWindow(current_user)
    if os.path.exists(APP_ICON_PATH):
        main_window_ref.setWindowIcon(QIcon(APP_ICON_PATH))
    
    print("8. Показ главного окна...")
    main_window_ref.show()
    main_window_ref.raise_()
    main_window_ref.activateWindow()
    
    print(f"✅ Окно видно: {main_window_ref.isVisible()}")
    
    print("9. Загрузка контактов...")
    main_window_ref.load_contacts()
    
    print("✅ Мессенджер запущен!")


if __name__ == "__main__":
    main()
