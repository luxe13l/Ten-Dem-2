"""Менеджер иконок для Ten Dem."""
from __future__ import annotations
import os
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

# Путь к папке с иконками
ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")

# Список всех необходимых иконок
ICON_FILES = {
    "plus": "plus.svg",
    "attach": "attach.svg",
    "send": "send.svg",
    "settings": "settings.svg",
    "search": "search.svg",
    "back": "back.svg",
    "menu": "menu.svg",
    "reply": "reply.svg",
    "pin": "pin.svg",
    "forward": "forward.svg",
    "edit": "edit.svg",
    "delete": "delete.svg",
    "check": "check.svg",
    "double_check": "double_check.svg",
    "photo": "photo.svg",
    "video": "video.svg",
    "file": "file.svg",
    "poll": "poll.svg",
    "emoji": "emoji.svg",
    "mic": "mic.svg",
    "close": "close.svg",
    "arrow_right": "arrow_right.svg",
    "arrow_left": "arrow_left.svg",
    "download": "download.svg",
    "folder": "folder.svg",
    "chat": "chat.svg",
    "contact": "contact.svg",
    "group": "group.svg",
    "online": "online.svg",
    "offline": "offline.svg",
}

def get_icon(name: str, size: int = 22) -> QIcon:
    """
    Загружает иконку по имени.
    
    Args:
        name: Имя иконки (из ICON_FILES)
        size: Размер иконки в пикселях
    
    Returns:
        QIcon или пустой QIcon если файл не найден
    """
    if name not in ICON_FILES:
        print(f"⚠️ Иконка '{name}' не найдена в ICON_FILES")
        return QIcon()
    
    filename = ICON_FILES[name]
    filepath = os.path.join(ICONS_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ Файл иконки не найден: {filepath}")
        return QIcon()
    
    icon = QIcon(filepath)
    icon.addFile(filepath, QSize(size, size))
    return icon

def get_icon_path(name: str) -> str:
    """Возвращает полный путь к файлу иконки."""
    if name not in ICON_FILES:
        return ""
    return os.path.join(ICONS_DIR, ICON_FILES[name])

def check_all_icons() -> dict:
    """Проверяет наличие всех иконок и возвращает отчёт."""
    report = {"found": [], "missing": []}
    
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