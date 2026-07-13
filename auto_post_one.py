#!/usr/bin/env python3
"""Generate one fresh 'On This Day' fact card and post it immediately to the Page.

Designed to be triggered by a scheduled GitHub Actions job (see
.github/workflows/auto_post.yml) -- each run fetches a new fact for today
(skipping ones already used, tracked in content_pipeline/used_facts.json),
renders the card, posts it, and updates the dedupe log so the next scheduled
run (later today, or tomorrow) gets a different fact. No queue to run dry.
"""
import argparse
import datetime
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "content_pipeline"))
sys.path.insert(0, str(BASE_DIR / "fb_auto_poster"))

from dotenv import load_dotenv

import fetch_facts
import make_cards
import generate_captions
import post_to_facebook


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Generate the card but don't post it")
    args = parser.parse_args()

    load_dotenv(BASE_DIR / "fb_auto_poster" / ".env")

    today = datetime.date.today()
    events = fetch_facts.fetch_events(today.month, today.day)
    used = fetch_facts.load_used()
    facts = fetch_facts.pick_facts(events, count=1, used=used)

    if not facts:
        print("No new facts available for today (all used already) -- skipping this run.")
        return

    fact = facts[0]
    used.add(fact["text"][:80])
    fetch_facts.save_used(used)

    out_dir = BASE_DIR / "content_pipeline" / "output" / "_auto"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = out_dir / f"post_{stamp}.png"

    handle = os.environ.get("PAGE_HANDLE", "@YourPage")
    make_cards.make_card(fact, image_path, page_handle=handle)

    caption = generate_captions.build_caption(fact, index=hash(fact["text"]) % len(generate_captions.HOOKS))

    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    result = post_to_facebook.post_photo_to_page(page_id, token, image_path, caption, dry_run=args.dry_run)
    print(f"{'[dry-run] Would post' if args.dry_run else 'Posted'} fact ({fact['region']}, {fact['year']}): {result}")


if __name__ == "__main__":
    main()
