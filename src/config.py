import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "").strip()

IG_USERNAME = os.getenv("IG_USERNAME", "").strip()
IG_PASSWORD = os.getenv("IG_PASSWORD", "").strip()

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "60"))
PER_USER_SLEEP = float(os.getenv("PER_USER_SLEEP", "1.0"))

def assert_no_rapidapi():
    # RapidAPI kullanılmayacak. Env set edilmişse bile boşsa sorun yok.
    if (os.getenv("RAPIDAPI_KEY") or "").strip() or (os.getenv("RAPIDAPI_HOST") or "").strip():
        raise RuntimeError("RapidAPI is disabled. Remove RAPIDAPI_* from workflow/env.")
