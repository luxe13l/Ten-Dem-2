"""Менеджер иконок для Ten Dem."""
from __future__ import annotations
import os
from PyQt6.QtGui import QIcon

# ✅ ПРАВИЛЬНЫЙ ПУТЬ — поднимаемся на 3 уровня вверх
def get_icons_dir():
    """Получает путь к папке с иконками."""
    # Текущий файл: Ten-Dem-3/src/utils/icons.py
    current_file = os.path.abspath(__file__)
    
    # Поднимаемся на 3 уровня вверх:
    # utils → src → Ten-Dem-3
    utils_dir = os.path.dirname(current_file)           # .../Ten-Dem-3/src/utils
    src_dir = os.path.dirname(utils_dir)                # .../Ten-Dem-3/src
    project_root = os.path.dirname(src_dir)             # .../Ten-Dem-3
    
    # Возвращаем путь к assets/icons
    return os.path.join(project_root, "assets", "icons")

ICONS_DIR = get_icons_dir()

# Полный список иконок
ICON_FILES = {
    "plus": "plus.svg",
    "attach": "attach.svg",
    "send": "send.svg",
    "settings": "settings.svg",
    "reply": "reply.svg",
    "pin": "pin.svg",
    "forward": "forward.svg",
    "edit": "edit.svg",
    "delete": "delete.svg",
    "check": "check.svg",
    "emoji": "emoji.svg",
    "chat": "chat.svg",
    "contact": "contact.svg",
    "folder": "folder.svg",
    "back": "back.svg",
    "close": "close.svg",
    "arrow_right": "arrow_right.svg",
    "arrow_left": "arrow_left.svg",
    "download": "download.svg",
    "group": "group.svg",
    "online": "online.svg",
    "offline": "offline.svg",
}

def get_icon(name: str, color: str = "#FFFFFF", size: int = 22) -> QIcon:
    """Загружает иконку по имени."""
    if name not in ICON_FILES:
        print(f"⚠️ Иконка '{name}' не найдена в ICON_FILES")
        return QIcon()
    
    filename = ICON_FILES[name]
    filepath = os.path.join(ICONS_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ Файл иконки не найден: {filepath}")
        return QIcon()
    
    icon = QIcon(filepath)
    
    if icon.isNull():
        print(f"⚠️ Не удалось загрузить иконку: {filepath}")
        return QIcon()
    
    return icon

def check_all_icons() -> dict:
    """Проверяет наличие всех иконок."""
    report = {"found": [], "missing": []}
    
    print(f"\n📁 Путь к иконкам: {ICONS_DIR}")
    print(f"📁 Путь существует: {os.path.exists(ICONS_DIR)}")
    print(f"📁 Файлы в папке: {os.listdir(ICONS_DIR) if os.path.exists(ICONS_DIR) else 'Папка не найдена'}\n")
    
    for name, filename in ICON_FILES.items():
        filepath = os.path.join(ICONS_DIR, filename)
        if os.path.exists(filepath):
            report["found"].append(name)
        else:
            report["missing"].append(name)
    
    return report

def print_icon_status():
    """Выводит статус всех иконок в консоль."""
    report = check_all_icons()
    
    print("\n=== СТАТУС ИКОНОК ===")
    print(f"✅ Найдено: {len(report['found'])}")
    print(f"❌ Отсутствует: {len(report['missing'])}")
    
    if report["missing"]:
        print("\nОтсутствующие иконки:")
        for name in report["missing"]:
            print(f"  - {name} ({ICON_FILES[name]})")
    
    print("======================\n")
    
    return len(report["missing"]) == 0