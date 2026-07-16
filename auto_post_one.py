#!/usr/bin/env python3
"""Generate one fresh fact card and post it immediately to the Page.

Mixes three free sources so content isn't limited to pure history:
  - Wikipedia Pageviews (what's genuinely popular/most-viewed right now --
    our "most engaged" signal, since Reddit's API is closed to new developers)
  - uselessfacts.jsph.pl (general "anything interesting" facts, any topic)
  - Wikipedia "On This Day" (date-anchored history facts, for variety)

Designed to be triggered by a scheduled GitHub Actions job (see
.github/workflows/auto_post.yml) -- each run fetches one new fact (skipping
ones already used, tracked in content_pipeline/used_facts.json), renders the
card, posts it, and updates the dedupe log. No queue to run dry.
"""
import argparse
import datetime
import os
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "content_pipeline"))
sys.path.insert(0, str(BASE_DIR / "fb_auto_poster"))

from dotenv import load_dotenv

import fetch_facts
import fetch_trending_facts
import fetch_viral_facts
import make_cards
import generate_captions
import post_to_facebook

# Viral (most-viewed-right-now) weighted highest since that's our "most engaged" proxy,
# general trending facts second, date-anchored history third for variety.
SOURCE_WEIGHTS = {"viral": 0.45, "trending": 0.30, "history": 0.25}


def get_one_fact(used):
    """Try sources in a weighted-random priority order, falling back through the rest if empty."""
    today = datetime.date.today()
    sources = list(SOURCE_WEIGHTS.keys())
    weights = list(SOURCE_WEIGHTS.values())
    order = []
    remaining = list(zip(sources, weights))
    while remaining:
        names, wts = zip(*remaining)
        pick = random.choices(names, weights=wts, k=1)[0]
        order.append(pick)
        remaining = [(n, w) for n, w in remaining if n != pick]

    for source in order:
        if source == "viral":
            facts = fetch_viral_facts.pick_viral_facts(count=1, used=used)
        elif source == "trending":
            facts = fetch_trending_facts.pick_trending_facts(count=1, used=used)
        else:
            events = fetch_facts.fetch_events(today.month, today.day)
            facts = fetch_facts.pick_facts(events, count=1, used=used)
        if facts:
            return facts[0]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Generate the card but don't post it")
    args = parser.parse_args()

    load_dotenv(BASE_DIR / "fb_auto_poster" / ".env")

    used = fetch_facts.load_used()
    fact = get_one_fact(used)

    if not fact:
        print("No new facts available from either source right now -- skipping this run.")
        return

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
    label = f"{fact['region']}, {fact['year']}" if fact.get("year") else fact["region"]
    print(f"{'[dry-run] Would post' if args.dry_run else 'Posted'} fact ({label}): {result}")


if __name__ == "__main__":
    main()
