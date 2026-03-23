import os

# Проверяем путь
icons_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
print(f"Путь к иконкам: {icons_path}")
print(f"Путь существует: {os.path.exists(icons_path)}")

# Список файлов
if os.path.exists(icons_path):
    files = os.listdir(icons_path)
    print(f"\nФайлы в папке:")
    for f in files:
        print(f"  - {f}")