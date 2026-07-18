#!/usr/bin/env python3
"""Generate and schedule up to ~29 days of compilation reels, using Facebook's
own native scheduling (scheduled_publish_time) -- same rationale as
schedule_batch.py, verified to work identically for /videos as it does for
/photos (publish_status: scheduled, published: False, confirmed via API).

Facebook's own limit: scheduled_publish_time must be 10 minutes to 30 days
from the time of the request, so this fills at most ~29 days per run.

Usage:
  python3 schedule_batch_reels.py --days 29 --handle "@NatureWonders9"
"""
import argparse
import datetime
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "content_pipeline"))
sys.path.insert(0, str(BASE_DIR / "fb_auto_poster"))

from dotenv import load_dotenv

from auto_post_one import get_one_fact
from schedule_batch import parse_times, build_slots
import fetch_facts
import make_cards
import make_reel
import post_to_facebook

MAX_DAYS = 29
FACTS_PER_REEL = 5
SECONDS_PER_FACT = 4


def main():
    parser = argparse.ArgumentParser(description="Batch-generate and schedule compilation reels")
    parser.add_argument("--days", type=int, default=MAX_DAYS)
    parser.add_argument("--times", default="06:00,18:00", help="Comma-separated local times, e.g. 06:00,18:00")
    parser.add_argument("--tz-offset-hours", type=float, default=5.5, help="IST = 5.5")
    parser.add_argument("--handle", default="@NatureWonders9")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.days > MAX_DAYS:
        print(f"Capping --days to {MAX_DAYS} (Facebook's scheduling window is 30 days max).")
        args.days = MAX_DAYS

    load_dotenv(BASE_DIR / "fb_auto_poster" / ".env")
    times = parse_times(args.times)
    slots = build_slots(args.days, times, args.tz_offset_hours)

    print(f"Scheduling {len(slots)} reel(s) across {args.days} day(s) x {len(times)} slot(s)/day.")

    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not args.dry_run and (not page_id or not token):
        print("Missing FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN in fb_auto_poster/.env", file=sys.stderr)
        sys.exit(1)

    used = fetch_facts.load_used()
    out_dir = BASE_DIR / "content_pipeline" / "output" / "_scheduled_reels_batch"
    out_dir.mkdir(parents=True, exist_ok=True)

    scheduled, skipped = 0, 0
    for i, ts in enumerate(slots, start=1):
        facts = []
        for _ in range(FACTS_PER_REEL):
            fact = get_one_fact(used)
            if not fact:
                break
            facts.append(fact)
            used.add(fact["text"][:80])

        if not facts:
            print(f"  [{i}/{len(slots)}] no new facts available -- skipping this slot")
            skipped += 1
            continue

        image_paths = []
        for j, fact in enumerate(facts, start=1):
            img_path = out_dir / f"reel_{ts}_{j}.png"
            make_cards.make_card_vertical(fact, img_path, page_handle=args.handle)
            image_paths.append(img_path)

        video_path = out_dir / f"reel_{ts}.mp4"
        music_path, attribution = make_reel.pick_track()
        make_reel.make_multi_reel(image_paths, video_path, per_image_duration=SECONDS_PER_FACT, music_path=music_path)

        caption = (
            f"{len(facts)} facts that'll make you say \"wait, really?\" 🤯 Follow for daily facts!\n\n"
            f"#Facts #DidYouKnow #Reels #OnThisDay\n\n"
            f"Music: {attribution}"
        )

        when = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        result = post_to_facebook.post_video_to_page(
            page_id, token, video_path, caption, dry_run=args.dry_run, scheduled_publish_time=ts
        )
        regions = ", ".join(sorted({f["region"] for f in facts}))
        print(f"  [{i}/{len(slots)}] {when} -- {len(facts)} facts ({regions}): {result}")
        scheduled += 1

        if not args.dry_run:
            time.sleep(2)

    fetch_facts.save_used(used)
    print(f"\nDone. Scheduled {scheduled} reel(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
