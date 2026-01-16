import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


SNAP_DIR = "snapshots"


def parse_targets(raw: str) -> List[str]:
    """
    TARGET_USERNAMES: "user1,user2,user3" veya satir satir da olabilir.
    """
    if not raw:
        return []
    raw = raw.replace("\n", ",")
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


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

    added = sorted(curr_set - prev_set)
    removed = sorted(prev_set - curr_set)

    return {"added": added, "removed": removed}


def fetch_current_data(username: str) -> Dict[str, Any]:
    """
    RapidAPI: Instagram Master API 2025
    Endpoint: /user/following?username_or_id_or_url=<username>
    """
    api_key = (os.environ.get("RAPIDAPI_KEY") or "").strip()
    api_host = (os.environ.get("RAPIDAPI_HOST") or "").strip()

    if not api_key or not api_host:
        raise RuntimeError("RAPIDAPI_KEY or RAPIDAPI_HOST missing")

    url = f"https://{api_host}/user/following"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
    }
    params = {"username_or_id_or_url": username}

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    # Beklenen: payload["data"]["users"] -> [{username: "..."}]
    users = (payload.get("data") or {}).get("users") or []
    following = sorted([u.get("username") for u in users if isinstance(u, dict) and u.get("username")])

    return {
        "username": username,
        "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
        "following": following,
        "following_count": len(following),
    }


def main() -> None:
    targets = parse_targets(os.environ.get("TARGET_USERNAMES", ""))

    if not targets:
        print("[ERROR] TARGET_USERNAMES is empty.")
        return

    print(f"--- Starting Tracker Job at {datetime.utcnow().isoformat()}Z ---")
    print(f"Targets: {targets}")

    for username in targets:
        try:
            curr = fetch_current_data(username)
            prev = load_snapshot(username)

            # İlk kez çalışıyorsa snapshot al
            if prev is None:
                save_snapshot(username, curr)
                telegram_send(
                    f"✅ İlk snapshot alındı: @{username}\n"
                    f"Following: {curr.get('following_count')}\n"
                    f"Zaman (UTC): {curr.get('fetched_at_utc')}"
                )
                print(f"[OK] First snapshot saved for {username}")
                time.sleep(1)
                continue

            diff = diff_following(prev, curr)

            if diff["added"] or diff["removed"]:
                save_snapshot(username, curr)

                msg = f"🔔 @{username} takip listesi değişti\n"
                msg += f"Following: {curr.get('following_count')}\n"
                msg += f"Zaman (UTC): {curr.get('fetched_at_utc')}\n\n"

                if diff["added"]:
                    msg += "➕ Takip etmeye başladı:\n"
                    msg += "\n".join(f"@{u}" for u in diff["added"]) + "\n\n"

                if diff["removed"]:
                    msg += "➖ Takibi bıraktı:\n"
                    msg += "\n".join(f"@{u}" for u in diff["removed"])

                telegram_send(msg)
                print(f"[OK] Following changes detected and notified for {username}")
            else:
                print(f"[OK] No following change for {username}")

            time.sleep(1)

        except Exception as e:
            print(f"[ERROR] Failed for {username}: {e}")

    print(f"--- Finished Tracker Job at {datetime.utcnow().isoformat()}Z ---")


if __name__ == "__main__":
    main()
