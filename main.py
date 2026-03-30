"""Ten Dem Messenger - Main Entry Point."""
from __future__ import annotations

import os
import sys
import threading
import traceback

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.database.local_store import load_store
from src.styles.themes import apply_theme

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ICON_PATH = os.path.join(APP_ROOT, "assets", "icons", "chat.svg")


def _install_global_exception_handler():
    """Показывает ошибку вместо молчаливого падения приложения."""
    default_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        try:
            QMessageBox.critical(
                None,
                "Критическая ошибка",
                f"{exc_type.__name__}: {exc_value}\n\nПодробности в консоли.",
            )
        except Exception:
            pass
        default_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook

    def _thread_hook(args):
        _hook(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thread_hook


def main():
    print("=== ЗАПУСК TEN DEM ===")

    # 1) Firebase
    from src.database.firebase_client import init_firebase
    try:
        init_firebase()
    except Exception as exc:
        print(f"⚠️ Firebase не инициализирован: {exc}")
        print("   Приложение запустится в ограниченном режиме")

    # 2) Локальный кеш
    from src.database.local_cache import init_cache
    try:
        init_cache()
    except Exception as exc:
        print(f"⚠️ Ошибка инициализации кеша: {exc}")

    # 3) Yandex Storage
    from src.database.yandex_storage import init_yandex_storage
    try:
        init_yandex_storage()
    except Exception as exc:
        print(f"⚠️ Yandex Storage не подключен: {exc}")
        print("   Загрузка файлов будет недоступна")

    # 4) .env
    from dotenv import load_dotenv
    load_dotenv()

    # 5) QApplication
    app = QApplication(sys.argv)
    _install_global_exception_handler()
    app.setApplicationName("Ten Dem")
    app.setApplicationVersion("1.0.0")

    # 6) Тема
    store = load_store()
    first_user_uid = next(iter(store.get("settings", {})), None)
    saved_theme = "dark"
    if first_user_uid:
        saved_theme = store["settings"][first_user_uid].get("theme", "dark")
    apply_theme(app, saved_theme)

    # 7) Иконка
    if os.path.exists(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))

    # 8) Wizard
    try:
        from src.ui.registration_wizard import RegistrationWizard
        wizard = RegistrationWizard()
    except Exception as exc:
        print(f"❌ Ошибка создания окна регистрации: {exc}")
        traceback.print_exc()
        QMessageBox.critical(None, "Ошибка", f"Не удалось создать окно входа:\n{exc}")
        return

    main_window_ref = None

    def on_registration_complete(data):
        nonlocal main_window_ref
        print(f"✅ Авторизация завершена, данные: {data}")
        try:
            wizard.close()
            wizard.deleteLater()

            from src.models.user import User

            uid = data.get("uid", "")
            if not uid:
                import uuid as _uuid
                uid = f"local-{_uuid.uuid4().hex[:8]}"
                print(f"⚠️ UID не получен, создан временный: {uid}")

            current_user = User(
                uid=uid,
                phone=data.get("phone", ""),
                name=data.get("name", "") or "Пользователь",
                username=data.get("username", ""),
                surname=data.get("surname", ""),
                bio=data.get("bio", ""),
            )

            user_settings = store.get("settings", {}).get(current_user.uid, {})
            current_user.theme = user_settings.get("theme", "dark")
            current_user.username = user_settings.get("username", current_user.username)
            current_user.bio = user_settings.get("bio", current_user.bio)

            apply_theme(app, current_user.theme)

            if current_user.uid and not current_user.uid.startswith("local-"):
                try:
                    from src.database.users_db import update_user
                    update_user(
                        current_user.uid,
                        {
                            "uid": current_user.uid,
                            "phone": current_user.phone,
                            "name": current_user.name,
                            "username": current_user.username,
                            "bio": current_user.bio,
                            "theme": current_user.theme,
                            "status": "online",
                        },
                    )
                except Exception as db_err:
                    print(f"⚠️ Ошибка обновления статуса в Firebase: {db_err}")

            from src.ui.main_window import MainWindow
            main_window_ref = MainWindow(current_user)

            if os.path.exists(APP_ICON_PATH):
                main_window_ref.setWindowIcon(QIcon(APP_ICON_PATH))

            main_window_ref.show()
            main_window_ref.raise_()
            main_window_ref.activateWindow()
            app.processEvents()
            main_window_ref.load_chats()
            print("✅ Мессенджер запущен")

        except Exception as exc:
            print(f"💥 Критическая ошибка on_registration_complete: {exc}")
            traceback.print_exc()
            QMessageBox.critical(None, "Критическая ошибка", f"Приложение не смогло запуститься:\n{exc}")

    wizard.registration_complete.connect(on_registration_complete)
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
