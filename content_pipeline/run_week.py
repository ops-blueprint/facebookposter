#!/usr/bin/env python3
"""Generate a week's worth of daily fact-card batches in one command.

This is for the personal-profile workflow (Path A) where posting itself must
stay a human click in Facebook's native Schedule button -- this script just
means you only need to sit down and queue things up once every few days
instead of daily.

Produces one dated folder per day, each with its own fact(s) + captions, e.g.:
  output/2026-07-13/  output/2026-07-14/  ... output/2026-07-19/

Usage:
  python3 run_week.py --handle "@jhanavi.janu.m"
  python3 run_week.py --days 14 --per-day 2 --handle "@jhanavi.janu.m"
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import fetch_facts
import make_cards
import generate_captions


def generate_day(date, count, handle):
    out_dir = BASE_DIR / "output" / date.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    events = fetch_facts.fetch_events(date.month, date.day)
    used = fetch_facts.load_used()
    facts = fetch_facts.pick_facts(events, count, used)
    if not facts:
        print(f"  {date.isoformat()}: no new facts available, skipping")
        return None

    for f in facts:
        used.add(f["text"][:80])
    fetch_facts.save_used(used)
    (out_dir / "facts.json").write_text(json.dumps(facts, indent=2))

    for i, fact in enumerate(facts, start=1):
        make_cards.make_card(fact, out_dir / f"fact_{i}.png", page_handle=handle)

    blocks = []
    for i, fact in enumerate(facts, start=1):
        caption = generate_captions.build_caption(fact, i - 1)
        blocks.append(f"--- fact_{i}.png ---\n{caption}\n")
    (out_dir / "captions.txt").write_text("\n".join(blocks))

    print(f"  {date.isoformat()}: {len(facts)} fact(s) -> {out_dir}")
    return out_dir


def main():
    parser = argparse.ArgumentParser(description="Generate a week (or more) of daily fact batches")
    parser.add_argument("--days", type=int, default=7, help="How many days ahead to generate, starting today")
    parser.add_argument("--per-day", type=int, default=1, help="How many facts/images per day")
    parser.add_argument("--handle", default="@jhanavi.janu.m")
    parser.add_argument("--start", help="MM-DD to start from, defaults to today")
    args = parser.parse_args()

    if args.start:
        month, day = map(int, args.start.split("-"))
        start = datetime.date(datetime.date.today().year, month, day)
    else:
        start = datetime.date.today()

    print(f"Generating {args.days} day(s) x {args.per_day} fact(s)/day starting {start.isoformat()}:")
    written = []
    for offset in range(args.days):
        date = start + datetime.timedelta(days=offset)
        out_dir = generate_day(date, args.per_day, args.handle)
        if out_dir:
            written.append(out_dir)

    print(f"\nDone. {len(written)} day(s) of content ready under output/.")
    print("Open each folder and queue fact_1.png (+ its caption from captions.txt) into")
    print("Facebook's native Schedule button, dated for that folder's day.")


if __name__ == "__main__":
    main()
