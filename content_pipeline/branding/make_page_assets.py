#!/usr/bin/env python3
"""Generate a matching profile picture and cover photo for the Page.

Free, local, Pillow-only -- same visual system as the fact cards (dark
background, region accent colors) so the Page looks cohesive.

Usage:
  python3 make_page_assets.py --name "On This Day" --tagline "Daily history facts"
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Bundled fonts (not OS system fonts) so rendering is identical on macOS and on
# GitHub Actions' Ubuntu runners. Anton and Ubuntu are free, open-license (OFL/UFL).
FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
FONT_BLACK = FONT_DIR / "Anton-Regular.ttf"
FONT_BOLD = FONT_DIR / "Ubuntu-Bold.ttf"
FONT_REGULAR = FONT_DIR / "Ubuntu-Regular.ttf"

BG_TOP = (28, 24, 46)
BG_BOTTOM = (10, 10, 18)
REGIONS = [
    ("USA", (239, 68, 68)),
    ("UK", (59, 130, 246)),
    ("AUS", (250, 204, 21)),
    ("EUROPE", (168, 85, 247)),
]


def vertical_gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def make_profile_pic(out_path, size=800):
    img = vertical_gradient(size, size, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Outer ring split into 4 colored arcs, one per region -- ties the brand together
    ring_margin = 30
    ring_width = 26
    box = [ring_margin, ring_margin, size - ring_margin, size - ring_margin]
    arc_span = 360 / len(REGIONS)
    start = -90
    for _, color in REGIONS:
        draw.arc(box, start=start, end=start + arc_span - 6, fill=color, width=ring_width)
        start += arc_span

    # Centered monogram
    mono_font = ImageFont.truetype(str(FONT_BLACK), 260)
    text = "OTD"
    bbox = draw.textbbox((0, 0), text, font=mono_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - 40), text, font=mono_font, fill=(255, 255, 255))

    # Tagline below monogram
    tag_font = ImageFont.truetype(str(FONT_BOLD), 46)
    tagline = "ON THIS DAY"
    bbox2 = draw.textbbox((0, 0), tagline, font=tag_font)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((size - tw2) / 2, size / 2 + 130), tagline, font=tag_font, fill=(200, 200, 210))

    img.save(out_path, quality=95)
    print(f"Wrote {out_path} ({size}x{size})")


def make_cover_photo(out_path, name="On This Day", tagline="Daily history facts", w=1640, h=624):
    img = vertical_gradient(w, h, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # top accent bar
    draw.rectangle([0, 0, w, 10], fill=(168, 85, 247))

    margin = 90

    title_font = ImageFont.truetype(str(FONT_BLACK), 110)
    draw.text((margin, 150), name, font=title_font, fill=(255, 255, 255))

    tagline_font = ImageFont.truetype(str(FONT_REGULAR), 42)
    draw.text((margin, 300), tagline, font=tagline_font, fill=(210, 210, 220))

    # region chips along the bottom
    chip_font = ImageFont.truetype(str(FONT_BOLD), 30)
    x = margin
    y = h - 110
    pad_x, pad_y = 26, 14
    gap = 24
    for label, color in REGIONS:
        bbox = draw.textbbox((0, 0), label, font=chip_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        chip_w, chip_h = tw + pad_x * 2, th + pad_y * 2
        draw.rounded_rectangle([x, y, x + chip_w, y + chip_h], radius=chip_h / 2, outline=color, width=3)
        draw.text((x + pad_x, y + pad_y - bbox[1]), label, font=chip_font, fill=color)
        x += chip_w + gap

    img.save(out_path, quality=95)
    print(f"Wrote {out_path} ({w}x{h})")


def main():
    parser = argparse.ArgumentParser(description="Generate Page profile picture + cover photo")
    parser.add_argument("--name", default="On This Day")
    parser.add_argument("--tagline", default="Daily history facts • USA · UK · Australia · Europe")
    parser.add_argument("--out-dir", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    make_profile_pic(out_dir / "profile_pic.png")
    make_cover_photo(out_dir / "cover_photo.png", name=args.name, tagline=args.tagline)


if __name__ == "__main__":
    main()
