#!/usr/bin/env python3
"""One command: fetch today's facts, render cards, write captions.

Output lands in content_pipeline/output/<YYYY-MM-DD>/ as:
  fact_1.png ... fact_N.png
  captions.txt   (caption text per image, in order)

Usage:
  python3 run_pipeline.py --count 5 --handle "@jhanavi.janu.m"
  python3 run_pipeline.py --date 12-25 --count 3   # generate for a specific date ahead of time
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


def main():
    parser = argparse.ArgumentParser(description="Run the full facts content pipeline")
    parser.add_argument("--date", help="MM-DD, defaults to today")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--handle", default="@jhanavi.janu.m")
    args = parser.parse_args()

    if args.date:
        month, day = map(int, args.date.split("-"))
        label = f"{datetime.date.today().year}-{month:02d}-{day:02d}"
    else:
        today = datetime.date.today()
        month, day = today.month, today.day
        label = today.isoformat()

    out_dir = BASE_DIR / "output" / label
    out_dir.mkdir(parents=True, exist_ok=True)
    facts_path = out_dir / "facts.json"

    print(f"== Fetching facts for {month:02d}-{day:02d} ==")
    events = fetch_facts.fetch_events(month, day)
    used = fetch_facts.load_used()
    facts = fetch_facts.pick_facts(events, args.count, used)
    if not facts:
        print("No new facts available for this date (all used already).", file=sys.stderr)
        sys.exit(1)
    for f in facts:
        used.add(f["text"][:80])
    fetch_facts.save_used(used)
    facts_path.write_text(json.dumps(facts, indent=2))
    for f in facts:
        print(f"  {f['flag']} [{f['region']}] {f['year']}: {f['text'][:80]}")

    print(f"\n== Rendering {len(facts)} cards ==")
    for i, fact in enumerate(facts, start=1):
        img_path = out_dir / f"fact_{i}.png"
        make_cards.make_card(fact, img_path, page_handle=args.handle)
        print(f"  wrote {img_path}")

    print("\n== Writing captions ==")
    blocks = []
    for i, fact in enumerate(facts, start=1):
        caption = generate_captions.build_caption(fact, i - 1)
        blocks.append(f"--- fact_{i}.png ---\n{caption}\n")
    captions_path = out_dir / "captions.txt"
    captions_path.write_text("\n".join(blocks))
    print(f"  wrote {captions_path}")

    print(f"\nDone. Open this folder and queue the images into Facebook's native Schedule button:\n  {out_dir}")


if __name__ == "__main__":
    main()
