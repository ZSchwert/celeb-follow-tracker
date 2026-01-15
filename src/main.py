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


def diff_dict(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basit bir diff: degisen alanlari raporlar.
    (Takip listesi gibi buyuk alanlar varsa, onu ayrı mantikla diff etmek daha iyi.)
    """
    changes = {}
    keys = set(prev.keys()) | set(curr.keys())
    for k in sorted(keys):
        pv = prev.get(k, None)
        cv = curr.get(k, None)
        if pv != cv:
            changes[k] = {"before": pv, "after": cv}
    return changes


def fetch_current_data(username: str) -> Dict[str, Any]:
    """
    BURASI 'data kaynagi' noktasi.

    - Eğer repo içinde zaten bir instagram_client / scraper varsa, onu burada kullan.
    - Ben burada Instagram korumalarini aşan/private endpoint kodu vermiyorum.
    - Bu fonksiyonun tek görevi: username için "o anki datayı" döndürmek.

    Örnek olarak sadece timestamp + username dönüyorum.
    Sen burayı kendi çalışan modülünle dolduracaksın.
    """
    return {
        "username": username,
        "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
        # Buraya senin ürettiğin alanlar gelecek:
        # "following": [...],
        # "followers_count": 123,
        # "following_count": 456,
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
            if prev is None:
                save_snapshot(username, curr)
                telegram_send(
                    f"✅ İlk snapshot alındı: @{username}\n"
                    f"Zaman (UTC): {curr.get('fetched_at_utc')}"
                )
                print(f"[OK] First snapshot saved for {username}")
                continue

            changes = diff_dict(prev, curr)
            if changes:
                save_snapshot(username, curr)
                msg = (
                    f"🔔 Değişiklik var: @{username}\n"
                    f"Zaman (UTC): {curr.get('fetched_at_utc')}\n\n"
                    f"Değişen alanlar:\n{json.dumps(changes, ensure_ascii=False, indent=2)}"
                )
                telegram_send(msg)
                print(f"[OK] Changes detected and notified for {username}")
            else:
                print(f"[OK] No change for {username}")

            # küçük bekleme (rate-limit vs. varsa iyi gelir)
            time.sleep(1)

        except Exception as e:
            print(f"[ERROR] Failed for {username}: {e}")

    print(f"--- Finished Tracker Job at {datetime.utcnow().isoformat()}Z ---")


if __name__ == "__main__":
    main()
