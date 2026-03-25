"""Локальный кэш на SQLite для снижения нагрузки на Firebase."""
import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache.db")

def get_connection():
    """Получает подключение к SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_cache():
    """Инициализирует таблицы кэша."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            chat_id TEXT,
            from_uid TEXT,
            to_uid TEXT,
            text TEXT,
            message_type TEXT,
            file_url TEXT,
            file_name TEXT,
            status TEXT,
            created_at TIMESTAMP,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY,
            phone TEXT,
            name TEXT,
            username TEXT,
            surname TEXT,
            status TEXT,
            avatar_url TEXT,
            theme TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            last_message TEXT,
            last_message_time TIMESTAMP,
            unread_count INTEGER DEFAULT 0,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Локальный кэш SQLite инициализирован")

def cache_messages(messages: List[Dict[str, Any]]):
    """Сохраняет сообщения в кэш."""
    if not messages:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for msg in messages:
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (message_id, chat_id, from_uid, to_uid, text, message_type, file_url, file_name, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg.get('id') or msg.get('message_id'),
            msg.get('chat_id') or msg.get('to_uid'),
            msg.get('from_uid'),
            msg.get('to_uid'),
            msg.get('text'),
            msg.get('message_type', 'text'),
            msg.get('file_url'),
            msg.get('file_name'),
            msg.get('status', 'sent'),
            msg.get('created_at') or datetime.utcnow().isoformat()
        ))
    
    conn.commit()
    conn.close()

def get_cached_messages(chat_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    """Получает сообщения из кэша."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM messages 
        WHERE chat_id = ? OR from_uid = ?
        ORDER BY created_at DESC 
        LIMIT ?
    """, (chat_id, chat_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def cache_user(user: Dict[str, Any]):
    """Сохраняет пользователя в кэш."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO users 
        (uid, phone, name, username, surname, status, avatar_url, theme)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.get('uid'),
        user.get('phone'),
        user.get('name'),
        user.get('username'),
        user.get('surname'),
        user.get('status', 'offline'),
        user.get('avatar_url'),
        user.get('theme', 'dark')
    ))
    
    conn.commit()
    conn.close()

def get_cached_user(uid: str) -> Optional[Dict[str, Any]]:
    """Получает пользователя из кэша."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None