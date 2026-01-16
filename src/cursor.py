import os
import json
from typing import List, Tuple

STATE_PATH = os.path.join("state", "cursor.json")

def _ensure_state_dir():
    os.makedirs("state", exist_ok=True)

def load_cursor() -> int:
    _ensure_state_dir()
    if not os.path.exists(STATE_PATH):
        return 0
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("cursor", 0))
    except Exception:
        return 0

def save_cursor(cursor: int) -> None:
    _ensure_state_dir()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"cursor": int(cursor)}, f, ensure_ascii=False, indent=2)

def take_batch(targets: List[str], cursor: int, batch_size: int) -> Tuple[List[str], int]:
    if not targets:
        return [], 0
    n = len(targets)
    cursor = max(0, min(cursor, n))
    batch = targets[cursor: cursor + batch_size]
    next_cursor = cursor + batch_size
    if next_cursor >= n:
        next_cursor = 0
    return batch, next_cursor
