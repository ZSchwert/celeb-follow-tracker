import time
import schedule
import datetime
from .config import CELEBRITIES
from .instagram_client import InstagramClient
from .twitter_client import TwitterClient
from .tracker import Tracker

def run_tracker_job():
    print(f"--- Starting Tracker Job at {datetime.datetime.now()} ---")

    insta_client = InstagramClient()
    twitter_client = TwitterClient()
    tracker = Tracker()

    for celebrity in CELEBRITIES:
        print(f"Checking {celebrity}...")

        # 1. Fetch current following
        current_following = insta_client.get_following(celebrity)

        if current_following is None:
            print(f"  Skipping {celebrity} due to fetch error.")
            continue

        if not current_following and insta_client.is_logged_in:
            # If logged in and got empty list, it might be an error or private account or really 0 following.
            # But since we return None on exception, this means we successfully fetched 0 followings.
            print(f"  Warning: {celebrity} appears to be following 0 people.")

        # 2. Load previous data
        latest_file = tracker.get_latest_file(celebrity)
        old_following = []
        if latest_file:
            try:
                data = tracker.load_data(latest_file)
                old_following = data.get("following", [])
            except Exception as e:
                print(f"  Error loading previous data for {celebrity}: {e}")

        # 3. Compare if we have previous data
        if old_following:
            new_follows, unfollows = tracker.compare(old_following, current_following)

            if new_follows:
                print(f"  Found {len(new_follows)} new follows.")
                for new_user in new_follows:
                    msg = f"🚨 UPDATE: @{celebrity} started following @{new_user} on Instagram!"
                    twitter_client.post_tweet(msg)

            if unfollows:
                print(f"  Found {len(unfollows)} unfollows.")
                for old_user in unfollows:
                    msg = f"🚨 UPDATE: @{celebrity} unfollowed @{old_user} on Instagram."
                    twitter_client.post_tweet(msg)

            if not new_follows and not unfollows:
                print("  No changes detected.")
        else:
            print("  No previous data found. Saving initial data.")

        # 4. Save current data
        tracker.save_data(celebrity, current_following)

    print("--- Job Finished ---")

def main():
    # Run once immediately
    run_tracker_job()

    # Schedule to run every 6 hours
    schedule.every(6).hours.do(run_tracker_job)

    print("Scheduler started. Running every 6 hours...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
