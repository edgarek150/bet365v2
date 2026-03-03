#!/bin/bash
cd "$(dirname "$0")"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -x "$CHROME" ]; then
    echo "ERROR: Chrome not found at: $CHROME"
    exit 1
fi

echo "Using Chrome: $CHROME"

# --- Kill previous Chrome on port 9222 ---
pkill -f "chrome.*remote-debugging-port=9222" 2>/dev/null
sleep 1

# --- Start Chrome ---
"$CHROME" \
    --remote-debugging-port=9222 \
    --no-first-run \
    --no-default-browser-check \
    --disable-default-apps \
    --user-data-dir=/tmp/chrome-scraper \
    &

sleep 3

# --- Start scraper ---
python3 main.py >> scraper.log 2>&1
