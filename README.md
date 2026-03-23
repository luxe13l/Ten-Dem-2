# Ten Dem Messenger

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4.2-green.svg)](https://pypi.org/project/PyQt6/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange)](https://firebase.google.com/)

**Ten Dem** — это десктопный мессенджер с минималистичным интерфейсом, вдохновлённым Telegram. Написан на Python с использованием PyQt6 и Firebase Firestore в качестве серверной части. Проект демонстрирует чистую архитектуру, реальное время, красивый UI и готов к расширению.

## ✨ Особенности

- 🔐 **Упрощённый вход** по имени пользователя (в реальном проекте заменяется на Firebase Phone Auth)
- 💬 **Общий чат** (комната "general") с сообщениями в реальном времени
- 👥 **Список контактов** — все пользователи, когда-либо входившие
- 🎨 **Telegram-подобный дизайн**:
  - Свои сообщения — синие справа
  - Чужие — серые слева
  - Скруглённые углы (15px)
  - Время под сообщением
  - Круглые аватарки (заглушки)
- ⚡ **Живые обновления** через слушатель Firestore
- 📁 **Чистая архитектура** (модули auth, database, models, ui, utils)
- 🖼 **Векторные иконки** в формате SVG

## 🛠️ Технологии

- Python 3.8+
- PyQt6 — графический интерфейс
- Firebase Admin SDK — доступ к Firestore
- Firestore — хранение сообщений и пользователей
- Pillow — обработка изображений (аватары)
- Requests — для REST API Firebase (в будущем)

## 🚀 Установка и запуск

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/yourname/tendem-messenger.git
   cd tendem-messenger