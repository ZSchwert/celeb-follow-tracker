import os

# RapidAPI
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "")  # örn: instagram-master-api-2025.p.rapidapi.com

# Telegram (zaten sende var)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Hedef kullanıcılar (virgülle)
TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "")
