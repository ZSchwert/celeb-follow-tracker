import tweepy
from .config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET,
    TWITTER_BEARER_TOKEN
)

class TwitterClient:
    def __init__(self):
        self.client = None
        if TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET:
            try:
                self.client = tweepy.Client(
                    consumer_key=TWITTER_API_KEY,
                    consumer_secret=TWITTER_API_SECRET,
                    access_token=TWITTER_ACCESS_TOKEN,
                    access_token_secret=TWITTER_ACCESS_SECRET,
                    bearer_token=TWITTER_BEARER_TOKEN
                )
                print("Twitter client initialized.")
            except Exception as e:
                print(f"Failed to initialize Twitter client: {e}")
        else:
            print("Twitter credentials missing. Twitter posting will be skipped (Mock Mode).")

    def post_tweet(self, message):
        """
        Posts a tweet with the given message.
        """
        if not self.client:
            print(f"[MOCK TWEET]: {message}")
            return

        try:
            response = self.client.create_tweet(text=message)
            print(f"Tweet posted successfully: {response.data['id']}")
        except Exception as e:
            print(f"Error posting tweet: {e}")
