import instaloader
import time
import random
from config import INSTAGRAM_USER, INSTAGRAM_PASSWORD

class InstagramClient:
    def __init__(self):
        self.L = instaloader.Instaloader()
        self.is_logged_in = False
        if INSTAGRAM_USER and INSTAGRAM_PASSWORD:
            try:
                self.L.login(INSTAGRAM_USER, INSTAGRAM_PASSWORD)
                self.is_logged_in = True
                print(f"Logged in as {INSTAGRAM_USER}")
            except Exception as e:
                print(f"Failed to login: {e}")
        else:
            print("No Instagram credentials provided. Running in mock mode for following lists.")

    def get_following(self, username):
        """
        Fetches the list of usernames that the target user follows.
        Returns a list of strings (usernames), or None if an error occurs.
        """
        if not self.is_logged_in:
             # Mock data if not logged in
             print(f"Mocking data for {username} (Login required for real data)")
             return self._get_mock_following(username)

        try:
            # Add a small delay to avoid hitting rate limits too fast if calling in a loop
            time.sleep(random.uniform(2, 5))
            profile = instaloader.Profile.from_username(self.L.context, username)
            followees = profile.get_followees()
            # Iterating over the generator to get all usernames
            return [followee.username for followee in followees]
        except Exception as e:
            print(f"Error fetching data for {username}: {e}")
            return None

    def _get_mock_following(self, username):
        # Return a dummy list for testing.
        base_list = ["dummy_friend_1", "dummy_friend_2", "brand_account_1"]
        if username == "selenagomez":
             return base_list + ["taylorswift"]
        return base_list
