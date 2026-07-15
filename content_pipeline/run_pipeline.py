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
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from run_week import generate_day  # shared mixed history + trending logic


def main():
    parser = argparse.ArgumentParser(description="Run the full facts content pipeline for a single day")
    parser.add_argument("--date", help="MM-DD, defaults to today")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--handle", default="@jhanavi.janu.m")
    args = parser.parse_args()

    if args.date:
        month, day = map(int, args.date.split("-"))
        date = datetime.date(datetime.date.today().year, month, day)
    else:
        date = datetime.date.today()

    print(f"== Generating {args.count} fact(s) for {date.isoformat()} ==")
    out_dir = generate_day(date, args.count, args.handle)
    if not out_dir:
        print("No new facts available for this date (all used already).", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. Open this folder and queue the images into Facebook's native Schedule button:\n  {out_dir}")


if __name__ == "__main__":
    main()
