#!/usr/bin/env python3
"""Auto-post the next queued image+caption to a Facebook PAGE via the Graph API.

This only works for Facebook Pages -- the Graph API cannot post to personal
profiles (Meta removed that in 2018 and never brought it back). See
../content_pipeline/README.md for the personal-profile workflow instead.

Designed to be triggered by a free scheduler (e.g. a GitHub Actions cron job)
once per desired posting slot. Each run posts exactly ONE item from the queue
so consecutive scheduled runs naturally spread posts out over time.

Queue format (matches content_pipeline's output so you can point --queue-dir
straight at a content_pipeline/output/<date>/ folder):
  queue/
    fact_1.png
    fact_2.png
    captions.txt      # "--- fact_1.png ---\n<caption text>\n\n--- fact_2.png ---\n..."

Required environment variables (put them in a local .env file, never commit it):
  FB_PAGE_ID
  FB_PAGE_ACCESS_TOKEN   (a long-lived Page access token, see ../fb_auto_poster/README.md)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
GRAPH_API_VERSION = "v20.0"


def parse_captions(captions_path: Path) -> dict:
    """Parse a captions.txt into {filename: caption_text}."""
    if not captions_path.exists():
        return {}
    content = captions_path.read_text()
    blocks = re.split(r"^---\s*(.+?)\s*---\s*$", content, flags=re.MULTILINE)
    # blocks[0] is leading whitespace/garbage; then alternates [filename, text, filename, text, ...]
    captions = {}
    for i in range(1, len(blocks), 2):
        filename = blocks[i].strip()
        text = blocks[i + 1].strip() if i + 1 < len(blocks) else ""
        captions[filename] = text
    return captions


def load_posted_log(log_path: Path) -> set:
    if log_path.exists():
        return set(json.loads(log_path.read_text()))
    return set()


def save_posted_log(log_path: Path, posted: set):
    log_path.write_text(json.dumps(sorted(posted), indent=2))


def next_queue_item(queue_dir: Path, posted: set):
    images = sorted(
        [p for p in queue_dir.glob("*.png") if p.name not in posted]
        + [p for p in queue_dir.glob("*.jpg") if p.name not in posted]
    )
    return images[0] if images else None


def post_photo_to_page(page_id: str, access_token: str, image_path: Path, caption: str, dry_run: bool = False):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/photos"
    if dry_run:
        print(f"[dry-run] Would POST {image_path.name} to {url} with caption:\n{caption}\n")
        return {"dry_run": True}

    with open(image_path, "rb") as f:
        files = {"source": f}
        data = {"caption": caption, "access_token": access_token}
        resp = requests.post(url, files=files, data=data, timeout=60)

    if not resp.ok:
        raise RuntimeError(f"Facebook API error {resp.status_code}: {resp.text}")
    return resp.json()


def post_video_to_page(page_id: str, access_token: str, video_path: Path, caption: str, dry_run: bool = False):
    """Upload a short video to a Page's /videos endpoint. Facebook auto-treats
    vertical short-form video uploaded this way as a Reel -- no separate Reels
    Publishing API needed for clips this size."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/videos"
    if dry_run:
        print(f"[dry-run] Would POST {video_path.name} to {url} with caption:\n{caption}\n")
        return {"dry_run": True}

    with open(video_path, "rb") as f:
        files = {"source": f}
        data = {"description": caption, "access_token": access_token}
        resp = requests.post(url, files=files, data=data, timeout=120)

    if not resp.ok:
        raise RuntimeError(f"Facebook API error {resp.status_code}: {resp.text}")
    return resp.json()


def main():
    load_dotenv(BASE_DIR / ".env")

    parser = argparse.ArgumentParser(description="Post the next queued image to a Facebook Page")
    parser.add_argument("--queue-dir", default=str(BASE_DIR / "queue"),
                         help="Folder containing images + captions.txt (can point at a content_pipeline output folder)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be posted, don't call the API")
    args = parser.parse_args()

    queue_dir = Path(args.queue_dir)
    if not queue_dir.exists():
        print(f"Queue dir not found: {queue_dir}", file=sys.stderr)
        sys.exit(1)

    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not args.dry_run and (not page_id or not access_token):
        print("Missing FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN. Set them in fb_auto_poster/.env "
              "(see fb_auto_poster/README.md) or use --dry-run to test without them.", file=sys.stderr)
        sys.exit(1)

    log_path = queue_dir / "posted_log.json"
    posted = load_posted_log(log_path)

    item = next_queue_item(queue_dir, posted)
    if item is None:
        print("Queue is empty -- nothing new to post.")
        return

    captions = parse_captions(queue_dir / "captions.txt")
    caption = captions.get(item.name, "")

    print(f"Posting {item.name} ...")
    result = post_photo_to_page(page_id, access_token, item, caption, dry_run=args.dry_run)
    print(f"Result: {result}")

    if not args.dry_run:
        posted.add(item.name)
        save_posted_log(log_path, posted)


if __name__ == "__main__":
    main()
