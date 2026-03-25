"""Ten Dem Messenger - Main Entry Point."""
from __future__ import annotations
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from src.styles.themes import apply_theme
from src.database.local_store import load_store

# Пути
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ICON_PATH = os.path.join(APP_ROOT, "assets", "icons", "chat.svg")

def main():
    print("=== ЗАПУСК TEN DEM ===")
    
    # 1. Инициализируем Firebase
    from src.database.firebase_client import init_firebase
    try:
        init_firebase()
    except Exception as e:
        print(f"⚠️ Firebase не инициализирован: {e}")
        print("   Приложение запустится в ограниченном режиме")
    
    # 2. Инициализируем локальный кэш
    from src.database.local_cache import init_cache
    init_cache()
    
    # 3. Инициализируем Yandex Storage
    from src.database.yandex_storage import init_yandex_storage
    try:
        init_yandex_storage()
    except Exception as e:
        print(f"⚠️ Yandex Storage не подключён: {e}")
        print("   Загрузка файлов будет недоступна")
    
    # 4. Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # 5. Создаём QApplication
    print("3. Создание QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Ten Dem")
    app.setApplicationVersion("1.0.0")
    
    # 6. Загружаем настройки темы
    store = load_store()
    first_user_uid = next(iter(store.get("settings", {})), None)
    saved_theme = "dark"
    if first_user_uid:
        saved_theme = store["settings"][first_user_uid].get("theme", "dark")
    
    apply_theme(app, saved_theme)
    
    # 7. Иконка приложения
    if os.path.exists(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))
    
    # 8. Показываем окно регистрации
    print("4. Создание окна регистрации...")
    from src.ui.registration_wizard import RegistrationWizard
    wizard = RegistrationWizard()
    
    # Ссылка на главное окно (чтобы закрыть wizard при успехе)
    main_window_ref = None
    
    def on_registration_complete(data):
        """Обработка завершения регистрации/входа"""
        nonlocal main_window_ref
        print(f"✅ Регистрация завершена: {data}")
        
        wizard.close()
        wizard.deleteLater()
        
        from src.models.user import User
        current_user = User(
            uid=data.get('uid', '') or f"local-{__import__('uuid').uuid4().hex[:8]}",
            phone=data.get('phone', ''),
            name=data.get('name', '') or 'Пользователь',
            username=data.get('username', ''),
            surname=data.get('surname', ''),
            bio=data.get('bio', ''),
        )
        
        user_settings = store.get("settings", {}).get(current_user.uid, {})
        current_user.theme = user_settings.get("theme", "dark")
        current_user.username = user_settings.get("username", current_user.username)
        current_user.bio = user_settings.get("bio", current_user.bio)
        apply_theme(app, current_user.theme)
        
        if current_user.uid:
            from src.database.users_db import update_user
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
        from src.ui.main_window import MainWindow
        main_window_ref = MainWindow(current_user)
        if os.path.exists(APP_ICON_PATH):
            main_window_ref.setWindowIcon(QIcon(APP_ICON_PATH))
        
        print("8. Показ главного окна...")
        main_window_ref.show()
        main_window_ref.raise_()
        main_window_ref.activateWindow()
        
        print(f"✅ Окно видно: {main_window_ref.isVisible()}")
        
        print("9. Загрузка чатов...")
        main_window_ref.load_chats()
        
        print("✅ Мессенджер запущен!")
    
    wizard.registration_complete.connect(on_registration_complete)
    
    print("5. Показ окна регистрации...")
    wizard.show()
    
    print("6. Запуск...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()