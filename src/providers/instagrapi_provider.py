import os
import time
from typing import Dict, Set, Tuple

from instagrapi import Client

SETTINGS_PATH = os.path.join("data", "ig_settings.json")


def _ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)


def get_client() -> Client:
    _ensure_dirs()

    ig_user = os.getenv("IG_USERNAME", "").strip()
    ig_pass = os.getenv("IG_PASSWORD", "").strip()
    if not ig_user or not ig_pass:
        raise RuntimeError("IG_USERNAME / IG_PASSWORD env boş. GitHub Secrets ekleyin.")

    cl = Client()

    # cached settings varsa yükle
    if os.path.exists(SETTINGS_PATH):
        try:
            cl.load_settings(SETTINGS_PATH)
        except Exception:
            pass

    # login
    try:
        cl.login(ig_user, ig_pass)
    except Exception:
        cl = Client()
        cl.login(ig_user, ig_pass)

    # settings dump
    try:
        cl.dump_settings(SETTINGS_PATH)
    except Exception:
        pass

    return cl


def get_user_pk_and_following_count(cl: Client, username: str) -> Tuple[int, int]:
    info = cl.user_info_by_username(username)
    return info.pk, int(info.following_count)


def fetch_following_usernames(cl: Client, user_pk: int) -> Set[str]:
    data: Dict[int, object] = cl.user_following(user_pk, amount=0)
    usernames: Set[str] = set()
    for u in data.values():
        uname = getattr(u, "username", None)
        if uname:
            usernames.add(str(uname))
    return usernames


def polite_sleep(i: int) -> None:
    time.sleep(1.0 + (i % 5) * 0.2)
