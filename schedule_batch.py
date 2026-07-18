#!/usr/bin/env python3
"""Generate and schedule up to ~30 days of posts in one run, using Facebook's
own native post scheduling (scheduled_publish_time) -- not GitHub Actions cron.

Why: GitHub Actions' `schedule:` trigger is "best-effort" and can be delayed by
hours (confirmed on this repo). Facebook's own scheduling has no such problem --
once a post is uploaded with a scheduled_publish_time, Facebook's own servers
publish it at that exact moment, so posting time no longer depends on any
external scheduler's precision at all.

Facebook's own limit: scheduled_publish_time must be 10 minutes to 30 days
from the time of the request. So this script can fill at most ~29 days per
run (kept under 30 for safety margin) -- repeat it roughly monthly to keep
the runway topped up indefinitely.

Usage:
  python3 schedule_batch.py --days 28 --handle "@NatureWonders9"
  python3 schedule_batch.py --days 28 --times 06:00,18:00 --tz-offset-hours 5.5
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
import fetch_facts
import make_cards
import generate_captions
import post_to_facebook

MAX_DAYS = 29  # stays safely under Facebook's 30-day scheduling ceiling
MIN_LEAD_MINUTES = 15  # stays safely above Facebook's 10-minute minimum


def parse_times(times_str):
    out = []
    for part in times_str.split(","):
        hh, mm = part.strip().split(":")
        out.append((int(hh), int(mm)))
    return out


def build_slots(days, times, tz_offset_hours):
    """Return a sorted list of unix timestamps (UTC) for each day x time slot,
    skipping any that fall inside the next MIN_LEAD_MINUTES."""
    now = datetime.datetime.now(datetime.timezone.utc)
    tz = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
    today_local = now.astimezone(tz).date()

    slots = []
    for day_offset in range(days):
        local_date = today_local + datetime.timedelta(days=day_offset)
        for hh, mm in times:
            local_dt = datetime.datetime(local_date.year, local_date.month, local_date.day, hh, mm, tzinfo=tz)
            utc_dt = local_dt.astimezone(datetime.timezone.utc)
            if utc_dt < now + datetime.timedelta(minutes=MIN_LEAD_MINUTES):
                continue
            if utc_dt > now + datetime.timedelta(days=30):
                continue
            slots.append(int(utc_dt.timestamp()))
    return sorted(slots)


def main():
    parser = argparse.ArgumentParser(description="Batch-generate and schedule posts via Facebook's native scheduler")
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

    print(f"Scheduling {len(slots)} posts across {args.days} day(s) x {len(times)} slot(s)/day.")

    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not args.dry_run and (not page_id or not token):
        print("Missing FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN in fb_auto_poster/.env", file=sys.stderr)
        sys.exit(1)

    used = fetch_facts.load_used()
    out_dir = BASE_DIR / "content_pipeline" / "output" / "_scheduled_batch"
    out_dir.mkdir(parents=True, exist_ok=True)

    scheduled, skipped = 0, 0
    for i, ts in enumerate(slots, start=1):
        fact = get_one_fact(used)
        if not fact:
            print(f"  [{i}/{len(slots)}] no new fact available -- skipping this slot")
            skipped += 1
            continue
        used.add(fact["text"][:80])

        when = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        image_path = out_dir / f"post_{ts}.png"
        make_cards.make_card(fact, image_path, page_handle=args.handle)
        caption = generate_captions.build_caption(fact, index=i)

        result = post_to_facebook.post_photo_to_page(
            page_id, token, image_path, caption, dry_run=args.dry_run, scheduled_publish_time=ts
        )
        label = f"{fact['region']}, {fact['year']}" if fact.get("year") else fact["region"]
        print(f"  [{i}/{len(slots)}] {when} -- {label}: {result}")
        scheduled += 1

        if not args.dry_run:
            time.sleep(2)  # stay well under Graph API rate limits across a long batch

    fetch_facts.save_used(used)
    print(f"\nDone. Scheduled {scheduled} post(s), skipped {skipped}.")


if __name__ == "__main__":
    main()
