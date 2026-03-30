# build.spec
from PyInstaller.utils.hooks import collect_all

# Сбор всех зависимостей PyQt6
datas, binaries, hiddenimports = collect_all('PyQt6')

a = Analysis(
    ['main.py'],
    datas=datas + [
        ('assets', 'assets'),
        ('firebase-key.json', 'firebase-key.json'),
        ('icons', 'icons'),
    ],
    binaries=binaries,
    hiddenimports=hiddenimports + [
        'firebase_admin',
        'boto3',
        'botocore',
        's3transfer',
        'urllib3',
        'certifi',
        'google.cloud.firestore',
        'google.cloud.storage',
    ],
    ...)

exe = EXE(
    a,
    name='TenDem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Сжатие (уменьшает размер)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = без чёрного окна терминала
    icon='icons/app.ico',  # Иконка
    version=None,
)