# Facebook Content Automation (free resources only)

History/trending-facts content system for the `jhanavi.janu.m` Facebook
presence, built around one hard platform constraint: **Facebook's API cannot
post to personal profiles** (removed in 2018, still true in 2026). Two paths
follow from that:

- **[content_pipeline/](content_pipeline/README.md)** — Path A. Free,
  local, generates real "On This Day" fact cards + captions for your
  existing personal profile. You queue the output into Facebook's native
  Schedule button (a few minutes, a few times a week) — the only
  ToS-compliant way to get content onto a personal profile ahead of time.

- **[fb_auto_poster/](fb_auto_poster/README.md)** — Path B. True zero-touch
  automation via the official Graph API, but only works for a **Facebook
  Page** (separate from your profile). Free Page, free Developer App, free
  GitHub Actions cron.

## Quickest path to your first batch

```bash
cd content_pipeline
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
python3 run_pipeline.py --count 5 --handle "@jhanavi.janu.m"
```

Then open `content_pipeline/output/<today's date>/`, and queue the images +
captions into Facebook's native post scheduler.

## Why not just browser-automate the personal profile?

Bots that log in and click "Post" on your behalf violate Facebook's Terms of
Service. On a monetized account the downside if flagged is a restriction or
loss of monetization eligibility — not worth it for a scheduling
convenience. This project intentionally avoids that route.
