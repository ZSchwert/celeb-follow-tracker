import os
import json
import time
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

SNAP_DIR = "snapshots"


def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


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
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()

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


def read_celeb_file(path: str) -> List[str]:
    """
    data/celebrities.txt:
    - bos satirlar olur
    - bazen 'zac efron' gibi space'li satirlar var -> IG username olamaz -> atiyoruz
    - bazen ayni isim tekrar -> unique yapacagiz
    """
    if not os.path.exists(path):
        raise RuntimeError(f"CELEB_FILE not found: {path}")

    out: List[str] = []
    seen = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if not u:
                continue
            # bosluklu veya tabli olanlari at (instagram username olamaz)
            if any(ch.isspace() for ch in u):
                continue
            # basit temizlik
            u = u.replace("@", "")
            if u and u not in seen:
                seen.add(u)
                out.append(u)

    return out


def pick_rotating_batch(items: List[str], batch_size: int, seed: int) -> List[str]:
    if not items:
        return []
    batch_size = max(1, min(batch_size, len(items)))

    # Her run farkli baslangic noktasi
    start = (seed * batch_size) % len(items)
    batch = []
    for i in range(batch_size):
        batch.append(items[(start + i) % len(items)])
    return batch


def fetch_current_data(username: str) -> Dict[str, Any]:
    api_key = (os.environ.get("RAPIDAPI_KEY") or "").strip()
    api_host = (os.environ.get("RAPIDAPI_HOST") or "").strip()
    if not api_key or not api_host:
        raise RuntimeError("RAPIDAPI_KEY or RAPIDAPI_HOST missing")

    url = f"https://{api_host}/user/following"
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": api_host}
    params = {"username_or_id_or_url": username}

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    users = (payload.get("data") or {}).get("users") or []
    following = sorted([u.get("username") for u in users if isinstance(u, dict) and u.get("username")])

    return {
        "username": username,
        "fetched_at_utc": now_utc(),
        "following": following,
        "following_count": len(following),
    }


def fetch_with_retries(username: str, max_retries: int, backoff_base: float) -> Dict[str, Any]:
    """
    429 gelirse bekleyip tekrar dene (exponential backoff).
    """
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return fetch_current_data(username)
        except requests.HTTPError as e:
            last_err = e
            status = getattr(e.response, "status_code", None)
            # 429 ise backoff
            if status == 429 and attempt < max_retries:
                sleep_s = backoff_base * (2 ** attempt)
                sleep_s = min(sleep_s, 60)  # 60s üstüne çıkma
                print(f"[RATE] 429 for {username}. sleeping {sleep_s:.1f}s then retry...")
                time.sleep(sleep_s)
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                sleep_s = backoff_base * (2 ** attempt)
                sleep_s = min(sleep_s, 60)
                print(f"[RETRY] error for {username}: {e}. sleeping {sleep_s:.1f}s then retry...")
                time.sleep(sleep_s)
                continue
            raise

    raise RuntimeError(f"Failed after retries for {username}: {last_err}")


def main() -> None:
    celeb_file = (os.environ.get("CELEB_FILE") or "data/celebrities.txt").strip()
    batch_size = int((os.environ.get("BATCH_SIZE") or "25").strip())
    seed = int((os.environ.get("BATCH_SEED") or "1").strip())

    per_user_sleep = float((os.environ.get("PER_USER_SLEEP") or "1.2").strip())
    max_retries = int((os.environ.get("RAPIDAPI_MAX_RETRIES") or "6").strip())
    backoff_base = float((os.environ.get("RAPIDAPI_BACKOFF_BASE") or "1.8").strip())

    all_targets = read_celeb_file(celeb_file)
    batch = pick_rotating_batch(all_targets, batch_size, seed)

    if not batch:
        print("[ERROR] No targets found.")
        return

    print(f"--- Starting Tracker Job at {now_utc()} ---")
    print(f"Total targets in file: {len(all_targets)} | Batch size: {len(batch)} | Seed: {seed}")
    print(f"Batch: {batch}")

    ok_count = 0
    err_count = 0

    for username in batch:
        try:
            curr = fetch_with_retries(username, max_retries=max_retries, backoff_base=backoff_base)
            prev = load_snapshot(username)

            if prev is None:
                save_snapshot(username, curr)
                # İlk snapshotta telegram istersen kapatiriz.
                telegram_send(f"✅ İlk snapshot: @{username}\nFollowing: {curr['following_count']}\nUTC: {curr['fetched_at_utc']}")
                print(f"[OK] First snapshot saved for {username}")
            else:
                diff = diff_following(prev, curr)
                if diff["added"] or diff["removed"]:
                    save_snapshot(username, curr)

                    msg = (
                        f"🔔 @{username} takip listesi değişti\n"
                        f"Following: {curr['following_count']}\n"
                        f"UTC: {curr['fetched_at_utc']}\n\n"
                    )
                    if diff["added"]:
                        msg += "➕ Takip etmeye başladı:\n" + "\n".join(f"@{u}" for u in diff["added"]) + "\n\n"
                    if diff["removed"]:
                        msg += "➖ Takibi bıraktı:\n" + "\n".join(f"@{u}" for u in diff["removed"])

                    telegram_send(msg)
                    print(f"[OK] Change detected for {username}")
                else:
                    print(f"[OK] No following change for {username}")

            ok_count += 1
            time.sleep(per_user_sleep)

        except Exception as e:
            err_count += 1
            print(f"[ERROR] Failed for {username}: {e}")

    print(f"--- Finished Tracker Job at {now_utc()} | ok={ok_count} err={err_count} ---")


if __name__ == "__main__":
    main()
