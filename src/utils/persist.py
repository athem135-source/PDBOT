import json
import os
from typing import Any, Dict, List

# Data file under src/data/chat_single.json (created on save if missing)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "chat_single.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_chat_history() -> List[Dict[str, Any]]:
    """Load chat messages from the single JSON file. Returns an empty list if missing/invalid."""
    try:
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        # Corrupt or unreadable file; start fresh
        return []


def save_chat_history(messages: List[Dict[str, Any]]) -> None:
    """Persist chat messages to the single JSON file."""
    _ensure_data_dir()
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(messages or [], f, ensure_ascii=False, indent=2)
    except Exception:
        # Ignore write errors for now; caller can decide how to handle
        pass


def clear_chat_history() -> None:
    """Delete the history file if it exists."""
    try:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
    except Exception:
        pass

# Backward-compatible aliases expected by some app versions
def load_chat() -> List[Dict[str, Any]]:
    return load_chat_history()


def save_chat(messages: List[Dict[str, Any]]) -> None:
    save_chat_history(messages)


def clear_chat() -> None:
    clear_chat_history()
