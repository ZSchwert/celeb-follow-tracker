name: Follow Tracker (Hourly)

on:
  workflow_dispatch:
  schedule:
    # Saat basi (UTC). TR saati fark etmez; her saat calisacak.
    - cron: "0 * * * *"

jobs:
  track:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Restore snapshots cache
        uses: actions/cache@v4
        with:
          path: snapshots
          key: snapshots-${{ github.run_id }}
          restore-keys: |
            snapshots-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Debug - list files
        run: |
          echo "PWD:"
          pwd
          echo "ROOT:"
          ls -la
          echo "SRC:"
          ls -la src || true
          echo "DATA:"
          ls -la data || true
          echo "SNAPSHOTS:"
          ls -la snapshots || true

      - name: Run tracker
        env:
          TARGET_USERNAMES: ${{ secrets.TARGET_USERNAMES }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          mkdir -p snapshots
          python src/main.py

      - name: Save snapshots cache
        uses: actions/cache@v4
        with:
          path: snapshots
          key: snapshots-${{ github.run_id }}
