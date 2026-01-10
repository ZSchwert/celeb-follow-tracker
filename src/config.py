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

# List of celebrities to track
CELEBRITIES = [
    "selenagomez",
    "cristiano",
    "ariana_grande",
    "kimkardashian",
    "beyonce",
    "kyliejenner",
    "therock",
    "kendalljenner",
    "justinbieber",
    "taylorswift",
    "jlo",
    "neymarjr",
    "leomessi",
    "nickiminaj",
    "mileycyrus",
    "katyperry",
    "kourtneykardash",
    "kevinhart4real",
    "theellenshow",
    "realmadrid",
    "fcbarcelona",
    "rihanna",
    "ddlovato",
    "zendaya",
    "drake"
]
