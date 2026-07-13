# Path A — Content Pipeline (free, runs locally)

Generates ready-to-post "On This Day" history fact cards for your Facebook
profile: real facts from Wikipedia's free public API, rendered into branded
images, with captions and hashtags already written.

This does **not** post anything for you — Facebook does not allow any tool
(free or paid) to auto-post to a personal profile. This pipeline produces the
content; you queue it into Facebook's own native scheduler (a few minutes,
a few times a week). See "Getting it onto Facebook" below.

## What it uses (all free, no API keys)
- Wikipedia's public "On This Day" REST API for real, dated history facts
- Local Python + Pillow to render the images (no design tool needed)
- macOS system fonts (Arial/Arial Black) already on your machine

## One-time setup

```bash
cd "content_pipeline"
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

## Daily/weekly use

Generate today's batch:
```bash
source ../.venv/bin/activate
python3 run_pipeline.py --count 5 --handle "@jhanavi.janu.m"
```

Generate a batch for a future date (handy for scheduling ahead, e.g. before a
trip):
```bash
python3 run_pipeline.py --date 12-25 --count 5 --handle "@jhanavi.janu.m"
```

Output lands in `output/<date>/`:
- `fact_1.png ... fact_N.png` — the post images
- `captions.txt` — matching caption + hashtags for each image, in order
- `facts.json` — the raw fact data (for reference/debugging)

The pipeline keeps `used_facts.json` so it never repeats a fact you've
already generated, even across regenerations.

## Getting it onto Facebook (the manual-light step)

Your profile has Professional Mode (that's what powers your monetization),
which gives you a native **Schedule** button in the post composer — same as
a Page has. Facebook does not let any external tool touch this for personal
profiles, so this last step has to be a human click:

1. Open Facebook → start a new post → check for the **Schedule** option in
   the composer (clock icon). If you don't see it, it's rolling out by
   region — try posting from desktop, or check Meta Business Suite
   (business.facebook.com) with this profile selected.
2. Upload `fact_1.png`, paste the matching block from `captions.txt`, set the
   date/time, repeat for each image.
3. Batch a week's worth in one 15-minute sitting.

## Tuning it to your voice
- Edit `HOOKS` and `QUESTIONS` in `generate_captions.py` to match how you'd
  actually talk to your audience.
- Edit `PALETTE` in `make_cards.py` to change colors per region.
- Some raw Wikipedia "on this day" events are heavy topics (deaths,
  disasters, crimes) — skim `facts.json` before posting and swap out
  anything that doesn't fit your page's tone by re-running with a higher
  `--count` and picking the ones you like.
- Widen/narrow the regions this favors by editing `REGION_KEYWORDS` in
  `fetch_facts.py`.
