#!/usr/bin/env python3
"""Generate 5 fresh facts, render each as a vertical Reel-format card, stitch
them into one compilation video with ffmpeg (each gets its own zoom segment,
one music track over the whole thing), and post it to the Page as a video.

Runs on the same schedule as auto_post_one.py (the static-image poster) --
see .github/workflows/auto_post_reels.yml.
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

from auto_post_one import get_one_fact
import fetch_facts
import make_cards
import make_reel
import post_to_facebook

FACTS_PER_REEL = 5
SECONDS_PER_FACT = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Generate the video but don't post it")
    parser.add_argument("--count", type=int, default=FACTS_PER_REEL)
    args = parser.parse_args()

    load_dotenv(BASE_DIR / "fb_auto_poster" / ".env")

    used = fetch_facts.load_used()
    facts = []
    for _ in range(args.count):
        fact = get_one_fact(used)
        if not fact:
            break
        facts.append(fact)
        used.add(fact["text"][:80])
    fetch_facts.save_used(used)

    if not facts:
        print("No new facts available from either source right now -- skipping this run.")
        return

    out_dir = BASE_DIR / "content_pipeline" / "output" / "_auto_reels"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    handle = os.environ.get("PAGE_HANDLE", "@YourPage")
    image_paths = []
    for i, fact in enumerate(facts, start=1):
        image_path = out_dir / f"reel_{stamp}_{i}.png"
        make_cards.make_card_vertical(fact, image_path, page_handle=handle)
        image_paths.append(image_path)

    video_path = out_dir / f"reel_{stamp}.mp4"
    music_path, attribution = make_reel.pick_track()
    make_reel.make_multi_reel(image_paths, video_path, per_image_duration=SECONDS_PER_FACT, music_path=music_path)

    regions = ", ".join(sorted({f["region"] for f in facts}))
    hashtags = " ".join(f"#{r.replace(' ', '')}" for r in {f["region"] for f in facts})
    caption = (
        f"{len(facts)} facts that'll make you say \"wait, really?\" 🤯 Follow for daily facts!\n\n"
        f"#Facts #DidYouKnow #Reels #OnThisDay {hashtags}\n\n"
        f"Music: {attribution}"
    )

    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    result = post_to_facebook.post_video_to_page(page_id, token, video_path, caption, dry_run=args.dry_run)
    print(f"{'[dry-run] Would post' if args.dry_run else 'Posted'} compilation reel "
          f"({len(facts)} facts: {regions}): {result}")


if __name__ == "__main__":
    main()
