# Celebrity Instagram Tracker

A system that tracks Instagram follow and unfollow activity for a list of celebrities and posts updates to Twitter/X.

## Features

- Tracks 25+ celebrities.
- Fetches public following lists using `instaloader`.
- Detects new follows and unfollows.
- Posts updates to Twitter using `tweepy`.
- Runs every 6 hours.
- Saves daily snapshots of following lists as JSON.

## Setup

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory with the following variables:
    ```env
    INSTAGRAM_USER=your_instagram_username
    INSTAGRAM_PASSWORD=your_instagram_password
    TWITTER_API_KEY=your_twitter_api_key
    TWITTER_API_SECRET=your_twitter_api_secret
    TWITTER_ACCESS_TOKEN=your_twitter_access_token
    TWITTER_ACCESS_SECRET=your_twitter_access_secret
    TWITTER_BEARER_TOKEN=your_twitter_bearer_token
    ```

    *Note: Instagram tracking requires a valid Instagram account login. Without credentials, the system runs in "Mock Mode" for testing.*

## Usage

Run the main script:

```bash
python -m src.main
```

The script will:
1.  Run an immediate check.
2.  Start a scheduler to run every 6 hours.
3.  Logs are printed to the console.

## Data

Data is stored in the `data/` directory. Each file is named `{username}_{YYYY-MM-DD}.json`.

## Structure

- `src/config.py`: Configuration and celebrity list.
- `src/instagram_client.py`: Handles Instagram data fetching.
- `src/twitter_client.py`: Handles posting to Twitter.
- `src/tracker.py`: Logic for data persistence and comparison.
- `src/main.py`: Entry point and scheduler.
