print("✅ NEW INSTAGRAPI MAIN ACTIVE")

import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests

from src.cursor import load_cursor, save_cursor, take_batch
from src.providers.instagrapi_provider import (
    get_client,
    get_user_pk_and_following_count,
    fetch_following_usernames,
    polite_sleep,
)

SNAP_DIR = "snapshots"
COUNTS_PATH = os.path.join("data", "following_counts.json")


def parse_targets(raw: str) -> List[str]:
    if not raw:
        return []
    raw = raw.replace("\n", ",")
    parts = [p.strip() for p in raw.split(",")]
    seen = set()
    out = []
    for p in parts:
        if not p:
            continue
        p = p.replace(" ", "")
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def load_snapshot(username: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(SNAP_DIR, f"{username}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_snapshot(username: str, data: Dict[str, Any]) -> None:
    os.makedirs(SNAP_DIR, exist_ok=True)
    path = os.path.join(SNAP_DIR, f"{username}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def telegram_send(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("[WARN] Telegram env missing. Skipping notify.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "disable_web_page_preview": True}

    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code != 200:
            print(f"[WARN] Telegram send failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[WARN] Telegram exception: {e}")


def diff_following(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, List[str]]:
    prev_set = set(prev.get("following", []) or [])
    curr_set = set(curr.get("following", []) or [])
    return {
        "added": sorted(curr_set - prev_set),
        "removed": sorted(prev_set - curr_set),
    }


def load_counts() -> Dict[str, int]:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(COUNTS_PATH):
        return {}
    try:
        with open(COUNTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: int(v) for k, v in data.items()}
    except Exception:
        return {}


def save_counts(counts: Dict[str, int]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(COUNTS_PATH, "w", encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=2)


def build_snapshot(username: str, following: Set[str]) -> Dict[str, Any]:
    following_list = sorted(list(following))
    return {
        "username": username,
        "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
        "following": following_list,
        "following_count": len(following_list),
    }


def main() -> None:
    targets = parse_targets(os.environ.get("TARGET_USERNAMES", ""))
    if not targets:
        print("[ERROR] TARGET_USERNAMES is empty.")
        return

    batch_size = int(os.environ.get("BATCH_SIZE", "30"))
    cursor = load_cursor()
    batch, next_cursor = take_batch(targets, cursor, batch_size)
    save_cursor(next_cursor)

    per_user_sleep = float(os.environ.get("PER_USER_SLEEP", "1.0"))

    print(f"--- Starting Tracker Job at {datetime.utcnow().isoformat()}Z ---")
    print(f"Total targets: {len(targets)} | Batch size: {batch_size} | Cursor: {cursor} -> {next_cursor}")
    print(f"Batch targets ({len(batch)}): {batch}")

    try:
        cl = get_client()
    except Exception as e:
        telegram_send(f"⚠️ IG login failed: {e}")
        print(f"[ERROR] IG login failed: {e}")
        return

    counts = load_counts()

    for i, username in enumerate(batch):
        try:
            user_pk, new_count = get_user_pk_and_following_count(cl, username)
            old_count = counts.get(username)

            if old_count is not None and old_count == new_count:
                print(f"[OK] No count change for {username} (still {new_count}) -> skip full list")
                time.sleep(per_user_sleep)
                continue

            following = fetch_following_usernames(cl, user_pk)
            curr = build_snapshot(username, following)
            prev = load_snapshot(username)

            if prev is None:
                save_snapshot(username, curr)
                telegram_send(f"✅ İlk snapshot: @{username}\nFollowing: {curr['following_count']}")
                print(f"[OK] First snapshot saved for {username}")
            else:
                diff = diff_following(prev, curr)
                if diff["added"] or diff["removed"]:
                    save_snapshot(username, curr)
                    msg = f"🔔 @{username} takip listesi değişti\nFollowing: {curr['following_count']}\n\n"
                    if diff["added"]:
                        msg += "➕ Takip etmeye başladı:\n" + "\n".join(f"@{u}" for u in diff["added"]) + "\n\n"
                    if diff["removed"]:
                        msg += "➖ Takibi bıraktı:\n" + "\n".join(f"@{u}" for u in diff["removed"])
                    telegram_send(msg)
                    print(f"[OK] Changes notified for {username}")
                else:
                    print(f"[OK] Count changed but no diff for {username}")

            counts[username] = int(new_count)
            polite_sleep(i)

        except Exception as e:
            telegram_send(f"⚠️ Tracker error @{username}: {e}")
            print(f"[ERROR] Failed for {username}: {e}")

        time.sleep(per_user_sleep)

    save_counts(counts)
    print(f"--- Finished Tracker Job at {datetime.utcnow().isoformat()}Z ---")


if __name__ == "__main__":
    main()
