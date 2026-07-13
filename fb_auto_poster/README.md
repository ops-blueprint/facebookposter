# Path B — Fully Automated Posting (Facebook Page, Graph API)

This is the only way to get genuine zero-touch, code-driven auto-posting on
Facebook. It requires a **Facebook Page** (not your personal profile — the
Graph API cannot post to personal profiles/timelines; Meta removed that in
2018 and it has never come back, confirmed as of 2026).

Everything below is free: the Page, the Developer App, the access token, and
the GitHub Actions cron that triggers posts.

## 1. Create a Facebook Page (free, ~5 min)

1. Go to Facebook → Pages → Create a Page.
2. Name it after your brand/persona (can reuse your profile's identity/photos).
3. This Page is separate from your personal profile — it's what the API is
   allowed to post to.

## 2. Create a Meta Developer App (free)

1. Go to https://developers.facebook.com/apps → Create App → choose "Other" →
   "Business" type.
2. In the app dashboard, add the **Facebook Login** and **Pages API**
   products.
3. Under App Roles, make sure your own Facebook account is an Admin/Developer
   of the app (it is by default since you created it).

## 3. Get a long-lived Page Access Token (free)

1. Go to https://developers.facebook.com/tools/explorer/
2. Select your App, then select your Page from the "User or Page" dropdown.
3. Request these permissions: `pages_show_list`, `pages_manage_posts`,
   `pages_read_engagement`.
4. Generate a short-lived token, then exchange it for a long-lived one (~60
   days) with this call (replace the placeholders):
   ```
   https://graph.facebook.com/v20.0/oauth/access_token?
     grant_type=fb_exchange_token&
     client_id=YOUR_APP_ID&
     client_secret=YOUR_APP_SECRET&
     fb_exchange_token=SHORT_LIVED_TOKEN
   ```
5. For a token that effectively never expires, use the long-lived user token
   above to fetch a **Page** access token via `GET /me/accounts` — Page
   tokens obtained this way don't expire as long as the user token stays
   valid and you don't change your Facebook password.
6. Find your Page ID: it's in your Page's "About" section, or via
   `GET /me/accounts`.

Put both values in `fb_auto_poster/.env` (copy `.env.example` first):
```
FB_PAGE_ID=123456789
FB_PAGE_ACCESS_TOKEN=EAAB...
```
**Never commit `.env`.**

## 4. Test locally

```bash
cd fb_auto_poster
python3 -m venv ../.venv        # skip if you already made this for content_pipeline
source ../.venv/bin/activate
pip install -r requirements.txt

# Dry run first -- prints what would be posted, calls no API
python3 post_to_facebook.py --queue-dir ../content_pipeline/output/2026-07-09 --dry-run

# Real post
python3 post_to_facebook.py --queue-dir ../content_pipeline/output/2026-07-09
```

Each run posts exactly **one** image from the queue folder (the earliest
file not yet marked posted in `posted_log.json`) with its matching caption
from `captions.txt`. Run it again and it posts the next one. This is
intentional — it's what makes scheduling trivial in step 5.

## 5. Automate the schedule for free (GitHub Actions cron)

GitHub Actions gives free scheduled runs (2,000 free minutes/month on a
private repo, unlimited on a public repo — this script needs seconds).

1. Push this project to a **private** GitHub repo (don't make `.env` public;
   `.gitignore` already excludes it).
2. In the repo, go to Settings → Secrets and variables → Actions, and add
   two repository secrets: `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN`.
3. Add `.github/workflows/post.yml`:

```yaml
name: Auto-post to Facebook Page
on:
  schedule:
    - cron: "0 14 * * *"   # daily at 14:00 UTC -- adjust to your best posting time
  workflow_dispatch: {}     # lets you trigger it manually too

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r fb_auto_poster/requirements.txt
      - env:
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python3 fb_auto_poster/post_to_facebook.py --queue-dir content_pipeline/output/QUEUE
```

4. Set up a `content_pipeline/output/QUEUE` folder that always holds the
   next batch (run `run_pipeline.py` weekly and copy/symlink the newest
   dated folder's contents in, or point `--queue-dir` at a fixed folder you
   refill manually/via another scheduled job).

From here, every day at your chosen time, GitHub's servers (not your laptop)
pull the next item from the queue and post it to your Page automatically.

## Connecting this back to your personal profile

Since the Page is a separate entity from your monetized profile, drive
your existing followers to it:
- Pin a post on your profile linking to the Page.
- Occasionally manually share a Page post to your profile (a normal user
  action — allowed, not automation).
- Cross-promote in your profile's bio/about section.

## What this does NOT do

It will not post to `facebook.com/jhanavi.janu.m` itself — no free or paid
tool can, per Facebook's platform rules. For that profile, use the
[content_pipeline](../content_pipeline/README.md) (Path A) to generate
content fast and queue it with Facebook's own native Schedule button.
