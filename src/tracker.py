import json
import os
import datetime
from config import DATA_DIR

class Tracker:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_latest_file(self, username):
        """
        Finds the most recent JSON file for a given username.
        Files are named: {username}_{YYYY-MM-DD}.json
        Returns the filepath or None.
        """
        files = [f for f in os.listdir(self.data_dir) if f.startswith(f"{username}_") and f.endswith(".json")]
        if not files:
            return None

        # Sort by date (filename)
        files.sort(reverse=True)
        return os.path.join(self.data_dir, files[0])

    def load_data(self, filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    def save_data(self, username, following_list):
        today = datetime.date.today().isoformat()
        filename = f"{username}_{today}.json"
        filepath = os.path.join(self.data_dir, filename)

        data = {
            "username": username,
            "date": today,
            "following": following_list,
            "timestamp": datetime.datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return filepath

    def compare(self, old_list, new_list):
        """
        Compares two lists of usernames.
        Returns:
            new_follows (set): Users in new_list but not in old_list.
            unfollows (set): Users in old_list but not in new_list.
        """
        old_set = set(old_list)
        new_set = set(new_list)

        new_follows = new_set - old_set
        unfollows = old_set - new_set

        return new_follows, unfollows
