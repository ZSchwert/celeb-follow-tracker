import os
from dotenv import load_dotenv

load_dotenv()

# Instagram Credentials
INSTAGRAM_USER = os.getenv("INSTAGRAM_USER")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Twitter Credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Data Directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Celebrities list: prefer env TARGET_USERNAMES, fallback to data/celebrities.txt, fallback to []
TARGET_USERNAMES = os.getenv("TARGET_USERNAMES", "").strip()

if TARGET_USERNAMES:
    CELEBRITIES = [u.strip() for u in TARGET_USERNAMES.split(",") if u.strip()]
else:
    CELEBRITIES_FILE = os.path.join(DATA_DIR, "celebrities.txt")
    try:
        with open(CELEBRITIES_FILE, "r", encoding="utf-8") as f:
            CELEBRITIES = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        CELEBRITIES = []


