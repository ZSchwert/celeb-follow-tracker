import os
import time
from typing import Dict, Set, Tuple

from instagrapi import Client


SETTINGS_PATH = os.path.join("data", "ig_settings.json")


def _ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)


def get_client() -> Client:
    """
    Creates an instagrapi Client, reuses cached settings if available,
    and performs login. Settings are dumped back to disk for caching.
    """
    _ensure_dirs()

    ig_user = os.getenv("IG_USERNAME", "").strip()
    ig_pass = os.getenv("IG_PASSWORD", "").strip()
    if not ig_user or not ig_pass:
        raise RuntimeError("IG_USERNAME / IG_PASSWORD env boş. GitHub Secrets ekleyin.")

    cl = Client()

    # Try loading cached settings (from actions/cache)
    if os.path.exists(SETTINGS_PATH):
        try:
            cl.load_settings(SETTINGS_PATH)
        except Exception:
            # settings bozuksa temiz başla
            pass

    # Login (prefer reusing session settings)
    try:
        cl.login(ig_user, ig_pass)
    except Exception:
        # Session invalid olabilir -> relogin
        cl = Client()
        cl.login(ig_user, ig_pass)

    # Dump settings for next runs (cache step will persist it)
    try:
        cl.dump_settings(SETTINGS_PATH)
    except Exception:
        pass

    return cl


def get_user_pk_and_following_count(cl: Client, username: str) -> Tuple[int, int]:
    info = cl.user_info_by_username(username)
    return info.pk, int(info.following_count)


def fetch_following_usernames(cl: Client, user_pk: int) -> Set[str]:
    """
    Returns the full following list as a set of usernames.
    """
    # instagrapi returns dict {pk: UserShort}
    data: Dict[int, object] = cl.user_following(user_pk, amount=0)
    usernames: Set[str] = set()

    for u in data.values():
        # UserShort has .username
        uname = getattr(u, "username", None)
        if uname:
            usernames.add(str(uname))

    return usernames


def polite_sleep(i: int) -> None:
    """
    Small delay to reduce bot-like behavior.
    """
    # 1.0s .. 1.8s arası basit jitter
    time.sleep(1.0 + (i % 5) * 0.2)
