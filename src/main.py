import sys
import os
import time
import schedule
import datetime

# Ensure we can import modules from /src when running from repo root (GitHub Actions)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../src
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import CELEBRITIES
from instagram_client import InstagramClient
from twitter_client import TwitterClient
from tracker import Tracker


def run_tracker_job():
    print(f"--- Starting Tracker Job at {datetime.datetime.now()} ---")

    insta_client = InstagramClient()
    twitter_client = TwitterClient()
    tracker = Tracker()

    for celebrity in CELEBRITIES:
        try:
            print(f"Checking {celebrity}...")

            # 1) Fetch current following
            current_following = insta_client.get_following(celebrity)

            # 2) Load previous following (if any) & compare
            previous_following = tracker.load_previous_following(celebrity)

            # 3) Detect changes
            added, removed = tracker.diff_following(previous_following, current_following)

            # 4) Notify if changed
            if added or removed:
                tracker.notify_changes(
                    celebrity=celebrity,
                    added=added,
                    removed=removed,
                    webhook_url=os.environ.get("WEBHOOK_URL", ""),
                )

            # 5) Save current snapshot
            tracker.save_following(celebrity, current_following)

        except Exception as e:
            print(f"[ERROR] Failed for {celebrity}: {e}")

    print(f"--- Finished Tracker Job at {datetime.datetime.now()} ---")


def main():
    # Run once immediately
    run_tracker_job()

    # Then schedule every 30 minutes (optional – workflow already runs on cron, but this is okay)
    schedule.every(30).minutes.do(run_tracker_job)


if __name__ == "__main__":
    main()
