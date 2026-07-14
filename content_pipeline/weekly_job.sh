#!/bin/bash
# Runs weekly via launchd (see ~/Library/LaunchAgents/com.jhanavi.fbcontent.weekly.plist).
# Generates next week's fact-card batch, then notifies + creates a Reminders.app task
# since queuing the posts into Facebook's native scheduler still needs a human click.
set -e

PROJECT_DIR="/Users/venumannuru/facebook-automation"
cd "$PROJECT_DIR"
source .venv/bin/activate

python3 content_pipeline/run_week.py --days 7 --handle "@jhanavi.janu.m"

osascript -e 'display notification "New week of fact cards is ready to schedule on Facebook." with title "Facebook Content Ready" sound name "Glass"' || true

osascript <<'EOF' || true
tell application "Reminders"
    set newReminder to make new reminder at end of reminders of default list
    set name of newReminder to "Queue this week's Facebook content (jhanavi.janu.m)"
    set body of newReminder to "Open content_pipeline/output/ in the Facebook project folder and schedule this week's fact cards using Facebook's native Schedule button (one post per day)."
    set due date of newReminder to (current date) + 1 * days
end tell
EOF
