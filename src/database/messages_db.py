"""Message storage with optimistic local updates and Firestore sync."""

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
        return "Фото"
    if message_type == MessageType.FILE.value:
        return message.get("file_name") or "Файл"
    if message_type == MessageType.VOICE.value:
        return "Голосовое сообщение"
    if message_type == MessageType.VIDEO.value:
        return "Видео"
    if message_type == MessageType.POLL.value:
        return f"Опрос: {message.get('text', '')}"
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
        print(f"Ошибка фоновой синхронизации Firebase: {exc}")


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
    return True


def get_messages(user_uid: str, contact_uid: str, limit: int = 50) -> list[dict[str, Any]]:
    local_messages = [m for m in _load_local_messages() if _participants_match(m, user_uid, contact_uid)]
    db = get_db()
    if db:
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
            merged = {item["id"]: item for item in remote}
            for item in local_messages:
                item.setdefault("reactions", {})
                item.setdefault("poll_options", [])
                item.setdefault("deleted_for", [])
                merged[item["id"]] = item
            result = list(merged.values())
            result.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
            return result[-limit:]
        except Exception as exc:
            print(f"Ошибка получения сообщений из Firebase: {exc}")
    local_messages.sort(key=lambda item: _sort_timestamp(item.get("timestamp")))
    return local_messages[-limit:]


def get_chat_summaries(current_uid: str) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
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


def listen_for_messages(user_uid: str, callback: Callable) -> Callable:
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
        db.collection("chats").document(chat_id).set(
            {
                "participants": [uid1, uid2],
                "last_message": _preview_message(message_data),
                "last_message_type": message_data.get("message_type", MessageType.TEXT.value),
                "last_message_time": message_data.get("timestamp", _now()),
                "updated_at": _now(),
            },
            merge=True,
        )
    except Exception as exc:
        print(f"Ошибка обновления сводки чата: {exc}")
