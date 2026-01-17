import json
import os
from typing import List, Tuple

CURSOR_PATH = os.path.join("data", "cursor.json")


def load_cursor() -> int:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(CURSOR_PATH):
        return 0
    try:
        with open(CURSOR_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("cursor", 0))
    except Exception:
        return 0


def save_cursor(cursor: int) -> None:
    os.makedirs("data", exist_ok=True)
    with open(CURSOR_PATH, "w", encoding="utf-8") as f:
        json.dump({"cursor": int(cursor)}, f, ensure_ascii=False, indent=2)


def take_batch(targets: List[str], cursor: int, batch_size: int) -> Tuple[List[str], int]:
    if not targets:
        return [], 0
    n = len(targets)
    cursor = cursor % n
    end = cursor + batch_size
    if end <= n:
        batch = targets[cursor:end]
        next_cursor = end % n
        return batch, next_cursor
    else:
        batch = targets[cursor:] + targets[: end % n]
        next_cursor = end % n
        return batch, next_cursor
