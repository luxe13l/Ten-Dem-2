"""Message storage with optimistic local updates and Firestore real-time sync."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Thread
from typing import Any, Callable
import uuid

from google.cloud.firestore_v1.base_query import FieldFilter

from src.database.firebase_client import get_db
from src.database.local_store import load_store, save_store
from src.models.message import MessageStatus, MessageType

QUICK_REACTIONS = ("❤️", "😂", "😮", "😢", "😡", "👍")


def _now() -> datetime:
    return datetime.now()


def _normalize_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return _now().replace(tzinfo=timezone.utc)


def _sort_timestamp(value: Any) -> float:
    return _normalize_datetime(value).timestamp()


def _normalize_type(message_type: MessageType | str) -> MessageType:
    return message_type if isinstance(message_type, MessageType) else MessageType(message_type or MessageType.TEXT.value)


def _normalize_status(status: MessageStatus | str) -> MessageStatus:
    return status if isinstance(status, MessageStatus) else MessageStatus(status or MessageStatus.SENT.value)


def _load_local_messages() -> list[dict[str, Any]]:
    return load_store().get("messages", [])


def _save_local_messages(messages: list[dict[str, Any]]) -> None:
    store = load_store()
    store["messages"] = messages
    save_store(store)


def _participants_match(message: dict[str, Any], uid1: str, uid2: str) -> bool:
    return {message.get("from_uid"), message.get("to_uid")} == {uid1, uid2}


def _preview_message(message: dict[str, Any]) -> str:
    message_type = message.get("message_type", MessageType.TEXT.value)
    if message_type == MessageType.PHOTO.value:
        return "Р¤РѕС‚Рѕ"
    if message_type == MessageType.FILE.value:
        return message.get("file_name") or "Р¤Р°Р№Р»"
    if message_type == MessageType.VOICE.value:
        return "Р“РѕР»РѕСЃРѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ"
    if message_type == MessageType.VIDEO.value:
        return "Р’РёРґРµРѕ"
    if message_type == MessageType.POLL.value:
        return f"РћРїСЂРѕСЃ: {message.get('text', '')}"
    return message.get("text", "")


def _sanitize_firestore_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    if "timestamp" in cleaned and cleaned["timestamp"] is None:
        cleaned["timestamp"] = _now()
    return cleaned


def _sync_to_firestore(message_id: str, action: str, payload: dict[str, Any] | None = None):
    db = get_db()
    if not db:
        return
    try:
        ref = db.collection("messages").document(message_id)
        if action == "create" and payload is not None:
            clean = _sanitize_firestore_payload(payload)
            ref.set(clean)
            _update_last_message(clean["from_uid"], clean["to_uid"], clean)
        elif action == "remove":
            ref.delete()
        elif action in {"edit", "delete", "reaction"} and payload is not None:
            ref.set(_sanitize_firestore_payload(payload), merge=True)
    except Exception as exc:
        print(f"РћС€РёР±РєР° С„РѕРЅРѕРІРѕР№ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё Firebase: {exc}")


def _spawn_sync(message_id: str, action: str, payload: dict[str, Any] | None = None):
    Thread(target=_sync_to_firestore, args=(message_id, action, payload), daemon=True).start()


def send_message(
    from_uid: str,
    to_uid: str,
    text: str = "",
    message_type: MessageType = MessageType.TEXT,
    file_url: str = "",
    file_name: str = "",
    file_size: int = 0,
    duration: int = 0,
    reply_to_id: str = "",
    forwarded_from_uid: str = "",
    disappears_in: int = 0,
    poll_options: list[str] | None = None,
) -> str | None:
    message_id = str(uuid.uuid4())
    record = {
        "id": message_id,
        "from_uid": from_uid,
        "to_uid": to_uid,
        "text": text,
        "message_type": _normalize_type(message_type).value,
        "timestamp": _now(),
        "status": _normalize_status(MessageStatus.SENT).value,
        "file_url": file_url,
        "file_name": file_name,
        "file_size": file_size,
        "duration": duration,
        "reply_to_id": reply_to_id,
        "forwarded_from_uid": forwarded_from_uid,
        "is_edited": False,
        "edited_at": None,
        "deleted_for": [],
        "disappears_at": _now() if disappears_in else None,
        "reactions": {},
        "poll_options": poll_options or [],
    }
    messages = _load_local_messages()
    messages.append(record)
    _save_local_messages(messages)
    _spawn_sync(message_id, "create", record)
    return message_id


def send_messages_batch(from_uid: str, to_uid: str, messages_payload: list[dict[str, Any]]) -> list[str]:
    created_ids: list[str] = []
    for payload in messages_payload:
        message_id = send_message(
            from_uid=from_uid,
            to_uid=to_uid,
            text=payload.get("text", ""),
            message_type=_normalize_type(payload.get("message_type", MessageType.TEXT.value)),
            file_url=payload.get("file_url", ""),
            file_name=payload.get("file_name", ""),
            file_size=payload.get("file_size", 0),
            duration=payload.get("duration", 0),
            reply_to_id=payload.get("reply_to_id", ""),
            forwarded_from_uid=payload.get("forwarded_from_uid", payload.get("from_uid", "")),
            poll_options=payload.get("poll_options", []),
        )
        if message_id:
            created_ids.append(message_id)
    return created_ids


def edit_message(message_id: str, new_text: str) -> bool:
    messages = _load_local_messages()
    for message in messages:
        if message.get("id") == message_id:
            message["text"] = new_text
            message["is_edited"] = True
            message["edited_at"] = _now()
            _save_local_messages(messages)
            _spawn_sync(message_id, "edit", {"text": new_text, "is_edited": True, "edited_at": message["edited_at"]})
            return True
    return False


def delete_message(message_id: str, for_everyone: bool = False, deleted_by: str = "") -> bool:
    messages = _load_local_messages()
    for index, message in enumerate(messages):
        if message.get("id") != message_id:
            continue
        if for_everyone:
            messages.pop(index)
            _save_local_messages(messages)
            _spawn_sync(message_id, "remove", None)
        else:
            deleted_for = list(message.get("deleted_for", []))
            if deleted_by and deleted_by not in deleted_for:
                deleted_for.append(deleted_by)
            message["deleted_for"] = deleted_for
            _save_local_messages(messages)
            _spawn_sync(message_id, "delete", {"deleted_for": deleted_for})
        return True
    return False


def toggle_reaction(message_id: str, emoji: str, user_uid: str) -> dict[str, list[str]] | None:
    if emoji not in QUICK_REACTIONS:
        return None
    messages = _load_local_messages()
    for message in messages:
        if message.get("id") != message_id:
            continue
        reactions = {key: list(value) for key, value in (message.get("reactions", {}) or {}).items()}
        users = reactions.setdefault(emoji, [])
        if user_uid in users:
            users.remove(user_uid)
        else:
            users.append(user_uid)
        if not users:
            reactions.pop(emoji, None)
        message["reactions"] = reactions
        _save_local_messages(messages)
        _spawn_sync(message_id, "reaction", {"reactions": reactions})
        return reactions
    return None


def mark_as_read(message_id: str) -> bool:
    messages = _load_local_messages()
    for message in messages:
        if message.get("id") == message_id:
            message["status"] = MessageStatus.READ.value
            _save_local_messages(messages)
            _spawn_sync(message_id, "edit", {"status": MessageStatus.READ.value})
            return True
    return False


def mark_chat_as_read(user_uid: str, contact_uid: str) -> bool:
    messages = _load_local_messages()
    changed = False
    for message in messages:
        if message.get("from_uid") == contact_uid and message.get("to_uid") == user_uid:
            message["status"] = MessageStatus.READ.value
            changed = True
    if changed:
        _save_local_messages(messages)
    db = get_db()
    if db:
        try:
            chat_id = "_".join(sorted([user_uid, contact_uid]))
            chat_ref = db.collection("chats").document(chat_id)
            chat_doc = chat_ref.get()
            if chat_doc.exists:
                data = chat_doc.to_dict() or {}
                unread_map = dict(data.get("unread_map", {}) or {})
                unread_map[user_uid] = 0
                chat_ref.set({"unread_map": unread_map}, merge=True)
        except Exception as exc:
            print(f"Ошибка обновления непрочитанных при чтении чата: {exc}")
    return True


def get_messages(user_uid: str, contact_uid: str, limit: int = 50) -> list[dict[str, Any]]:
    local_messages = [m for m in _load_local_messages() if _participants_match(m, user_uid, contact_uid)]
    local_messages.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))

    # Важно для скорости: если локальные сообщения уже есть, показываем их сразу,
    # а синхронизацию с сервером делаем в фоне.
    if local_messages:
        prefetch_chat_messages_async(user_uid, contact_uid, limit=max(120, limit))
        return local_messages[-limit:]

    # Первый вход в чат (кэша нет) — один раз ждём сервер и сохраняем локально.
    remote_messages = _fetch_remote_messages(user_uid, contact_uid)
    if remote_messages:
        _merge_chat_messages_into_local(user_uid, contact_uid, remote_messages)
        remote_messages.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
        return remote_messages[-limit:]

    return []


def _fetch_remote_messages(user_uid: str, contact_uid: str) -> list[dict[str, Any]]:
    db = get_db()
    if not db:
        return []
    try:
        docs = (
            db.collection("messages")
            .where(filter=FieldFilter("from_uid", "in", [user_uid, contact_uid]))
            .where(filter=FieldFilter("to_uid", "in", [user_uid, contact_uid]))
            .stream()
        )
        remote: list[dict[str, Any]] = []
        for doc in docs:
            data = doc.to_dict() or {}
            if _participants_match(data, user_uid, contact_uid):
                data["id"] = data.get("id") or doc.id
                data.setdefault("reactions", {})
                data.setdefault("poll_options", [])
                data.setdefault("deleted_for", [])
                remote.append(data)
        return remote
    except Exception as exc:
        print(f"Ошибка получения сообщений из Firebase: {exc}")
        return []


def _merge_chat_messages_into_local(user_uid: str, contact_uid: str, incoming: list[dict[str, Any]]) -> None:
    local_messages = _load_local_messages()
    others = [m for m in local_messages if not _participants_match(m, user_uid, contact_uid)]
    existing_chat = [m for m in local_messages if _participants_match(m, user_uid, contact_uid)]

    merged = {}
    for item in existing_chat:
        if item.get("id"):
            item.setdefault("reactions", {})
            item.setdefault("poll_options", [])
            item.setdefault("deleted_for", [])
            merged[item["id"]] = item
    for item in incoming:
        if item.get("id"):
            item.setdefault("reactions", {})
            item.setdefault("poll_options", [])
            item.setdefault("deleted_for", [])
            merged[item["id"]] = item

    merged_chat = list(merged.values())
    merged_chat.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
    _save_local_messages([*others, *merged_chat])


def prefetch_chat_messages(user_uid: str, contact_uid: str, limit: int = 150) -> None:
    remote = _fetch_remote_messages(user_uid, contact_uid)
    if not remote:
        return
    remote.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
    if limit > 0:
        remote = remote[-limit:]
    _merge_chat_messages_into_local(user_uid, contact_uid, remote)


def prefetch_chat_messages_async(user_uid: str, contact_uid: str, limit: int = 150) -> None:
    Thread(target=prefetch_chat_messages, args=(user_uid, contact_uid, limit), daemon=True).start()


def get_chat_summaries(current_uid: str) -> dict[str, dict[str, Any]]:
    """РџРѕР»СѓС‡Р°РµС‚ СЃРїРёСЃРѕРє С‡Р°С‚РѕРІ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР· Firebase + Р»РѕРєР°Р»СЊРЅРѕ"""
    summaries: dict[str, dict[str, Any]] = {}
    
    # 1. РЎРЅР°С‡Р°Р»Р° РїСЂРѕР±СѓРµРј РїРѕР»СѓС‡РёС‚СЊ РёР· Firebase (РєРѕР»Р»РµРєС†РёСЏ chats)
    db = get_db()
    if db:
        try:
            chats_ref = db.collection("chats")
            query = chats_ref.where("participants", "array_contains", current_uid)
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict() or {}
                participants = data.get("participants", [])
                
                # РќР°С…РѕРґРёРј СЃРѕР±РµСЃРµРґРЅРёРєР°
                contact_uid = None
                for p in participants:
                    if p != current_uid:
                        contact_uid = p
                        break
                
                if contact_uid:
                    unread_map = data.get("unread_map", {}) or {}
                    unread_for_me = unread_map.get(current_uid, data.get("unread_count", 0))
                    summaries[contact_uid] = {
                        "last_message": data.get("last_message", ""),
                        "last_message_type": data.get("last_message_type", "text"),
                        "timestamp": data.get("last_message_time"),
                        "unread_count": int(unread_for_me or 0),
                    }
        except Exception as exc:
            print(f"вљ пёЏ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ С‡Р°С‚РѕРІ РёР· Firebase: {exc}")
    
    # 2. Р•СЃР»Рё РёР· Firebase РїСѓСЃС‚Рѕ - Р±РµСЂС‘Рј РёР· Р»РѕРєР°Р»СЊРЅС‹С… СЃРѕРѕР±С‰РµРЅРёР№ (СЂРµР·РµСЂРІ)
    if not summaries:
        for message in _load_local_messages():
            if current_uid not in {message.get("from_uid"), message.get("to_uid")}:
                continue
            if current_uid in message.get("deleted_for", []):
                continue
            contact_uid = message.get("to_uid") if message.get("from_uid") == current_uid else message.get("from_uid")
            summary = summaries.setdefault(contact_uid, {"last_message": "", "timestamp": None, "unread_count": 0})
            timestamp = message.get("timestamp") or _now()
            if summary["timestamp"] is None or _sort_timestamp(timestamp) >= _sort_timestamp(summary["timestamp"]):
                summary["last_message"] = _preview_message(message)
                summary["timestamp"] = timestamp
            if message.get("to_uid") == current_uid and message.get("status") != MessageStatus.READ.value:
                summary["unread_count"] += 1
    
    return summaries


def listen_for_messages(user_uid: str, contact_uid: str, callback: Callable):
    """
    вњ… REAL-TIME РЎР›РЈРЁРђРўР•Р›Р¬: РЎР»СѓС€Р°РµС‚ Р±Р°Р·Сѓ РґР°РЅРЅС‹С… РІ СЂРµР°Р»СЊРЅРѕРј РІСЂРµРјРµРЅРё.
    РљР°Рє С‚РѕР»СЊРєРѕ РїРѕСЏРІР»СЏРµС‚СЃСЏ РЅРѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ РёР»Рё СЂРµР°РєС†РёСЏ вЂ” СЃСЂР°Р·Сѓ РІС‹Р·С‹РІР°РµС‚ callback.
    Р’РѕР·РІСЂР°С‰Р°РµС‚ С„СѓРЅРєС†РёСЋ РѕС‚РїРёСЃРєРё (unsubscribe).
    """
    db = get_db()
    if not db:
        return lambda: None
    
    try:
        # РЎРѕР·РґР°РµРј Р·Р°РїСЂРѕСЃ: СЃРѕРѕР±С‰РµРЅРёСЏ РјРµР¶РґСѓ РјРЅРѕР№ Рё РєРѕРЅС‚Р°РєС‚РѕРј
        query = (
            db.collection("messages")
            .where(filter=FieldFilter("from_uid", "in", [user_uid, contact_uid]))
            .where(filter=FieldFilter("to_uid", "in", [user_uid, contact_uid]))
            .order_by("timestamp", direction="DESCENDING")
            .limit(60)
        )
        
        # вњ… Р—РђРџРЈРЎРљРђР•Рњ РЎР›РЈРЁРђРўР•Р›Р¬ (on_snapshot)
        def on_snapshot(docs, changes, read_time):
            new_messages_data = []

            for change in changes:
                change_type = change.type.name
                data = change.document.to_dict() or {}
                data["id"] = change.document.id
                data["_change_type"] = change_type

                # Удаление для всех приходит как REMOVED.
                if change_type == "REMOVED":
                    new_messages_data.append(data)
                    continue

                # Если сообщение скрыто для текущего пользователя, отправляем как удаление.
                if user_uid in data.get("deleted_for", []):
                    data["_change_type"] = "REMOVED"
                    new_messages_data.append(data)
                    continue

                if change_type in {"ADDED", "MODIFIED"}:
                    new_messages_data.append(data)

            if new_messages_data:
                # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ РІСЂРµРјРµРЅРё (СЃР°РјС‹Рµ РЅРѕРІС‹Рµ СЃРІРµСЂС…Сѓ)
                new_messages_data.sort(key=lambda x: _sort_timestamp(x.get("timestamp")), reverse=True)
                callback(new_messages_data)
        
        # Р’РѕР·РІСЂР°С‰Р°РµРј С„СѓРЅРєС†РёСЋ РѕС‚РїРёСЃРєРё, С‡С‚РѕР±С‹ РѕСЃС‚Р°РЅРѕРІРёС‚СЊ СЃР»СѓС€Р°С‚РµР»СЏ РїСЂРё РІС‹С…РѕРґРµ РёР· С‡Р°С‚Р°
        return query.on_snapshot(on_snapshot)
        
    except Exception as exc:
        print(f"вќЊ РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ СЃР»СѓС€Р°С‚РµР»СЏ СЃРѕРѕР±С‰РµРЅРёР№: {exc}")
        return lambda: None


def listen_for_chat_updates(user_uid: str, callback: Callable):
    """
    Real-time listener списка чатов пользователя.
    Вызывает callback при любых изменениях чатов, чтобы UI обновил левый список.
    """
    db = get_db()
    if not db:
        return lambda: None

    try:
        query = db.collection("chats").where("participants", "array_contains", user_uid)

        def on_snapshot(docs, changes, read_time):
            changed = []
            for change in changes:
                data = change.document.to_dict() or {}
                data["id"] = change.document.id
                data["_change_type"] = change.type.name
                changed.append(data)
            if changed:
                callback(changed)

        return query.on_snapshot(on_snapshot)
    except Exception as exc:
        print(f"Ошибка создания слушателя чатов: {exc}")
        return lambda: None


def get_message_by_id(message_id: str) -> dict[str, Any] | None:
    for message in _load_local_messages():
        if message.get("id") == message_id:
            return message
    return None


def forward_messages(from_uid: str, selected_ids: list[str], new_to_uid: str) -> list[str]:
    originals = [get_message_by_id(message_id) for message_id in selected_ids]
    originals = [item for item in originals if item]
    originals.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
    payloads = []
    for original in originals:
        payloads.append(
            {
                "text": original.get("text", ""),
                "message_type": original.get("message_type", MessageType.TEXT.value),
                "file_url": original.get("file_url", ""),
                "file_name": original.get("file_name", ""),
                "file_size": original.get("file_size", 0),
                "duration": original.get("duration", 0),
                "forwarded_from_uid": original.get("from_uid", ""),
                "poll_options": original.get("poll_options", []),
            }
        )
    return send_messages_batch(from_uid, new_to_uid, payloads)


def get_media_gallery(user_uid: str, contact_uid: str, media_type: str = "photo") -> list[dict[str, Any]]:
    return [item for item in get_messages(user_uid, contact_uid, limit=500) if item.get("message_type") == media_type]


def _update_last_message(uid1: str, uid2: str, message_data: dict[str, Any]):
    db = get_db()
    if not db:
        return
    try:
        chat_id = "_".join(sorted([uid1, uid2]))
        chat_ref = db.collection("chats").document(chat_id)
        chat_doc = chat_ref.get()
        unread_map = {}
        if chat_doc.exists:
            unread_map = dict((chat_doc.to_dict() or {}).get("unread_map", {}) or {})
        unread_map[uid1] = 0
        unread_map[uid2] = int(unread_map.get(uid2, 0) or 0) + 1
        chat_ref.set(
            {
                "participants": [uid1, uid2],
                "last_message": _preview_message(message_data),
                "last_message_type": message_data.get("message_type", MessageType.TEXT.value),
                "last_message_time": message_data.get("timestamp", _now()),
                "updated_at": _now(),
                "unread_map": unread_map,
            },
            merge=True,
        )
    except Exception as exc:
        print(f"РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ СЃРІРѕРґРєРё С‡Р°С‚Р°: {exc}")


def delete_chat(user_uid: str, contact_uid: str) -> bool:
    """Удаляет чат и сообщения в фоне, чтобы не блокировать UI."""
    Thread(target=_delete_chat_remote, args=(user_uid, contact_uid), daemon=True).start()
    return True


def _delete_chat_remote(user_uid: str, contact_uid: str) -> None:
    db = get_db()
    if not db:
        return

    try:
        chat_id = "_".join(sorted([user_uid, contact_uid]))
        chat_ref = db.collection("chats").document(chat_id)
        chat_doc = chat_ref.get()

        if chat_doc.exists:
            chat_ref.delete()
            print(f"✅ Чат {chat_id} удалён")

        messages_ref = db.collection("messages")
        query1 = messages_ref.where("from_uid", "==", user_uid).where("to_uid", "==", contact_uid)
        query2 = messages_ref.where("from_uid", "==", contact_uid).where("to_uid", "==", user_uid)

        docs1 = query1.get()
        docs2 = query2.get()

        deleted_count = 0
        for doc in docs1:
            doc.reference.delete()
            deleted_count += 1

        for doc in docs2:
            doc.reference.delete()
            deleted_count += 1

        print(f"✅ Удалено {deleted_count} сообщений между {user_uid} и {contact_uid}")
    except Exception as exc:
        print(f"❌ Ошибка удаления чата: {exc}")

