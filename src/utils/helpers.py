"""
Вспомогательные функции для мессенджера Ten Dem
"""
import re
import hashlib
from datetime import datetime, timedelta


def format_time(dt):
    """Форматирует дату/время для отображения."""
    if not dt:
        return ""
    
    try:
        now = datetime.now()
        today = now.date()
        
        if hasattr(dt, 'date'):
            msg_date = dt.date()
        else:
            return ""
        
        if msg_date == today:
            return dt.strftime("%H:%M")
        
        yesterday = today - timedelta(days=1)
        if msg_date == yesterday:
            return "вчера"
        
        if msg_date.year == today.year:
            return dt.strftime("%d %b")
        
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return ""


def format_phone(phone):
    """Форматирует номер телефона."""
    try:
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        if not digits.startswith('7'):
            digits = '7' + digits
        
        digits = digits[:11]
        
        if len(digits) <= 1:
            return f"+{digits}"
        elif len(digits) <= 4:
            return f"+7 ({digits[1:]}"
        elif len(digits) <= 7:
            return f"+7 ({digits[1:4]}) {digits[4:]}"
        elif len(digits) <= 9:
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
    except Exception:
        return phone


def generate_avatar_color(name):
    """Генерирует пастельный цвет на основе имени."""
    try:
        if not name:
            return "#6c5ce7"
        
        hash_val = int(hashlib.md5(name.encode()).hexdigest(), 16) % 360
        
        h = hash_val
        s = 65
        l = 70
        
        c = (1 - abs(2 * l / 100 - 1)) * s / 100
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l / 100 - c / 2
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#6c5ce7"


def get_initials(name):
    """Получает инициалы из имени."""
    try:
        if not name:
            return "?"
        
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return parts[0][:2].upper() if len(parts[0]) >= 2 else parts[0].upper()
    except Exception:
        return "?"


def truncate(text, length=30):
    """Обрезает текст до заданной длины."""
    try:
        if not text or len(text) <= length:
            return text or ""
        return text[:length - 3] + "..."
    except Exception:
        return text