import json
import os
from typing import List, Tuple

CURSOR_PATH = os.path.join("state", "cursor.json")


def _ensure_dir() -> None:
    os.makedirs("state", exist_ok=True)


def load_cursor() -> int:
    _ensure_dir()
    if not os.path.exists(CURSOR_PATH):
        return 0
    try:
        with open(CURSOR_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("index", 0))
    except Exception:
        return 0


def save_cursor(index: int) -> None:
    _ensure_dir()
    with open(CURSOR_PATH, "w", encoding="utf-8") as f:
        json.dump({"index": int(index)}, f, ensure_ascii=False, indent=2)


def take_batch(items: List[str], start: int, batch_size: int) -> Tuple[List[str], int]:
    if not items:
        return [], 0
    n = len(items)
    start = start % n
    end = start + batch_size

    if end <= n:
        batch = items[start:end]
        next_index = end % n
        return batch, next_index

    # wrap around
    batch = items[start:] + items[: (end % n)]
    next_index = end % n
    return batch, next_index
