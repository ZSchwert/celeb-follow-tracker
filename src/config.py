import os

# Instagram login (instagrapi)
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_PASSWORD = os.getenv("IG_PASSWORD", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Targets
TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "")

# Batch config
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "60"))
PER_USER_SLEEP = float(os.getenv("PER_USER_SLEEP", "1.0"))
