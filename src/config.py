import os

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Hedef kullanıcılar
TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "")

# Instagram Login (instagrapi)
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_PASSWORD = os.getenv("IG_PASSWORD", "")

# 🚫 RapidAPI tamamen kapalı
RAPIDAPI_KEY = ""
RAPIDAPI_HOST = ""

def assert_no_rapidapi():
    # RapidAPI env set edilirse bile kullanımı yasakla
    if os.getenv("RAPIDAPI_KEY") or os.getenv("RAPIDAPI_HOST"):
        raise RuntimeError("RapidAPI is disabled. Remove RAPIDAPI_* from workflow/secrets.")
