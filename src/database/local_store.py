"""Local JSON-backed fallback storage for offline development."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict


_LOCK = RLock()
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_STORE_PATH = _DATA_DIR / "local_store.json"
_DEFAULT_DATA: Dict[str, Any] = {
    "users": {},
    "messages": [],
    "settings": {},
    "pinned_messages": {},
    "pinned_chats": {},
    "archived_chats": {},
    "deleted_chats": {},
    "muted_chats": {},
}


def _json_default(value: Any):
    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": value.isoformat()}
    raise TypeError(f"Unsupported value for JSON serialization: {type(value)!r}")


def _restore(value: Any):
    if isinstance(value, dict):
        if value.get("__type__") == "datetime":
            try:
                return datetime.fromisoformat(value["value"])
            except (KeyError, ValueError):
                return datetime.now()
        return {key: _restore(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_restore(item) for item in value]
    return value


def _ensure_store():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _STORE_PATH.exists():
        _STORE_PATH.write_text(
            json.dumps(_DEFAULT_DATA, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )


def load_store() -> Dict[str, Any]:
    with _LOCK:
        _ensure_store()
        raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        data = deepcopy(_DEFAULT_DATA)
        data.update(_restore(raw))
        return data


def save_store(data: Dict[str, Any]) -> None:
    with _LOCK:
        _ensure_store()
        _STORE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )


def update_store(mutator):
    with _LOCK:
        data = load_store()
        mutator(data)
        save_store(data)
        return data
