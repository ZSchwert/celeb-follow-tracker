import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

SNAP_DIR = "snapshots"

# Repo içindeki ünlü listesi dosyan
DEFAULT_CELEB_FILE = "data/celebrities.txt"


def parse_lines_to_usernames(text: str) -> List[str]:
    """
    Dosyadan/secret'tan gelen metni username listesine çevirir.
    - boş satırları atar
    - baş/son boşlukları kırpar
    - tekrarları kaldırır (sıralamayı bozmaz)
    - içinde boşluk olanları (örn "zac efron") SKIP eder (Instagram username boşluk içermez)
    """
    seen = set()
    out: List[str] = []

    for raw in text.splitlines():
        u = raw.strip()
        if not u:
            continue

        # Instagram username boşluk içermez. (Senin listede "zac efron", "eddie murphy" gibi var.)
        if " " in u:
            # istersen underscore'a çevirmek mümkün ama yanlış hesap riskini arttırır.
            # en güvenlisi skip edip loglamak.
            continue

        if u not in seen:
            seen.add(u)
            out.append(u)

    return out


def read_celebrities_file(path: str) -> List[str]:
    if not os.path.exists(path):
        print(f"[ERROR] Celeb file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return parse_lines_to_usernames(f.read())


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


def choose_batch(all_users: List[str], batch_size: int, seed: int) -> Tuple[List[str], int, int]:
    """
    Döner batch:
      seed = github.run_number gibi monoton artan bir sayı
      batch_index = seed % total_batches
    """
    if batch_size <= 0:
        batch_size = 15

    n = len(all_users)
    if n == 0:
        return [], 0, 0

    total_batches = (n + batch_size - 1) // batch_size
    batch_index = seed % total_batches

    start = batch_index * batch_size
    end = min(start + batch_size, n)
    return all_users[start:end], batch_index, total_batches


def rapidapi_get_following(username: str) -> Dict[str, Any]:
    """
    RapidAPI: Instagram Master API 2025
    Endpoint: /user/following?username_or_id_or_url=<username>

    429 olursa exponential backoff yapar.
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

    # Backoff ayarları
    max_retries = int(os.environ.get("RAPIDAPI_MAX_RETRIES", "6"))
    base_sleep = float(os.environ.get("RAPIDAPI_BACKOFF_BASE", "1.5"))  # 1.5s, 3s, 6s...

    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)

            if r.status_code == 429:
                # rate limit -> bekle ve tekrar dene
                wait = base_sleep * (2 ** attempt)
                print(f"[WARN] 429 rate limit for @{username}. Backoff {wait:.1f}s (attempt {attempt}/{max_retries})")
                time.sleep(wait)
                continue

            r.raise_for_status()
            return r.json()

        except Exception as e:
            last_exc = e
            # küçük bekleme (network vs)
            time.sleep(0.8)

    raise RuntimeError(f"RapidAPI failed for @{username} after retries: {last_exc}")


def fetch_current_data(username: str) -> Dict[str, Any]:
    payload = rapidapi_get_following(username)

    # Beklenen: payload["data"]["users"] -> [{username: "..."}]
    users = (payload.get("data") or {}).get("users") or []
    following = sorted(
        [
            u.get("username")
            for u in users
            if isinstance(u, dict) and u.get("username")
        ]
    )

    return {
        "username": username,
        "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
        "following": following,
        "following_count": len(following),
    }


def main() -> None:
    # 1) Listeyi nereden alacağız?
    # - Eğer secret TARGET_USERNAMES doluysa onu kullan
    # - Değilse data/celebrities.txt dosyasını kullan
    raw_targets = (os.environ.get("TARGET_USERNAMES") or "").strip()

    if raw_targets:
        all_users = parse_lines_to_usernames(raw_targets.replace(",", "\n"))
        source = "TARGET_USERNAMES secret"
    else:
        celeb_file = os.environ.get("CELEB_FILE", DEFAULT_CELEB_FILE)
        all_users = read_celebrities_file(celeb_file)
        source = celeb_file

    if not all_users:
        print("[ERROR] No usernames found (empty list).")
        return

    # 2) Batch ayarları
    batch_size = int(os.environ.get("BATCH_SIZE", "15"))
    seed = int(os.environ.get("BATCH_SEED", "0"))  # github.run_number gelecek

    batch, batch_index, total_batches = choose_batch(all_users, batch_size, seed)

    print(f"--- Starting Tracker Job at {datetime.utcnow().isoformat()}Z ---")
    print(f"Source: {source}")
    print(f"All users: {len(all_users)} | Batch size: {batch_size} | Batch: {batch_index+1}/{total_batches} | Seed: {seed}")
    print(f"Batch targets ({len(batch)}): {batch}")

    # İstersen her run başında kısa bir telegram info at:
    # telegram_send(f"⏱️ Tracker başladı | Batch {batch_index+1}/{total_batches} | {len(batch)} kişi")

    ok_count = 0
    fail_count = 0
    changed_count = 0

    for username in batch:
        try:
            curr = fetch_current_data(username)
            prev = load_snapshot(username)

            if prev is None:
                save_snapshot(username, curr)
                telegram_send(
                    f"✅ İlk snapshot: @{username}\n"
                    f"Following: {curr.get('following_count')}\n"
                    f"UTC: {curr.get('fetched_at_utc')}"
                )
                print(f"[OK] First snapshot saved for {username}")
                ok_count += 1
            else:
                diff = diff_following(prev, curr)

                if diff["added"] or diff["removed"]:
                    save_snapshot(username, curr)

                    msg = f"🔔 @{username} takip listesi değişti\n"
                    msg += f"Following: {curr.get('following_count')}\n"
                    msg += f"UTC: {curr.get('fetched_at_utc')}\n\n"

                    if diff["added"]:
                        msg += "➕ Takip etmeye başladı:\n"
                        msg += "\n".join(f"@{u}" for u in diff["added"]) + "\n\n"

                    if diff["removed"]:
                        msg += "➖ Takibi bıraktı:\n"
                        msg += "\n".join(f"@{u}" for u in diff["removed"])

                    telegram_send(msg)
                    print(f"[OK] Following changes detected for {username}")
                    changed_count += 1
                else:
                    print(f"[OK] No following change for {username}")

                ok_count += 1

            # genel limitlere takılmamak için küçük bekleme
            time.sleep(float(os.environ.get("PER_USER_SLEEP", "1.2")))

        except Exception as e:
            fail_count += 1
            print(f"[ERROR] Failed for {username}: {e}")

            # Fail olduğunda da bekle (kümülatif rate limit)
            time.sleep(2.0)

    summary = (
        f"✅ Tracker bitti\n"
        f"Batch: {batch_index+1}/{total_batches} | Users: {len(batch)}\n"
        f"OK: {ok_count} | Changed: {changed_count} | Failed: {fail_count}\n"
        f"UTC: {datetime.utcnow().isoformat()}Z"
    )
    print(summary)
    # İstersen summary telegram:
    telegram_send(summary)

    print(f"--- Finished Tracker Job at {datetime.utcnow().isoformat()}Z ---")


if __name__ == "__main__":
    main()
