#!/usr/bin/env python3
"""Turn a static vertical (1080x1920) card into a short Reel-format video.

Free, local, ffmpeg-only: a slow "Ken Burns" zoom on the still image, plus a
background track from a small bundled set of Creative Commons (CC-BY 4.0)
tracks by Kevin MacLeod (incompetech.com) -- not "trending" audio (Facebook's
trending sound library is an in-app-only feature with no API access, and
using an actual trending commercial song would be copyright infringement).
CC-BY requires attribution, which auto_post_reel.py appends to the caption.
"""
import argparse
import random
import subprocess
import tempfile
from pathlib import Path

DURATION = 6
FPS = 30
MUSIC_DIR = Path(__file__).resolve().parent / "music"

# filename -> (display title, attribution text required by the CC-BY 4.0 license)
TRACKS = {
    "Cheery_Monday.mp3": "Cheery Monday",
    "Monkeys_Spinning_Monkeys.mp3": "Monkeys Spinning Monkeys",
    "Pixel_Peeker_Polka_-_faster.mp3": "Pixel Peeker Polka (faster)",
    "Merry_Go.mp3": "Merry Go",
    "Local_Forecast_-_Elevator.mp3": "Local Forecast (Elevator)",
}


def pick_track():
    filename = random.choice(list(TRACKS.keys()))
    title = TRACKS[filename]
    attribution = f'"{title}" by Kevin MacLeod (incompetech.com) — Licensed under CC BY 4.0'
    return MUSIC_DIR / filename, attribution


def make_reel(image_path, out_path, duration=DURATION, fps=FPS, music_path=None):
    image_path = str(image_path)
    out_path = str(out_path)
    frames = duration * fps

    if music_path is None:
        music_path, _ = pick_track()
    music_path = str(music_path)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", music_path,
        "-vf",
        f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.15)':d={frames}:s=1080x1920:fps={fps}",
        "-af", f"atrim=0:{duration},afade=t=out:st={duration - 0.8}:d=0.8,volume=0.7",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-c:a", "aac", "-shortest",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-2000:]}")
    return out_path


def make_multi_reel(image_paths, out_path, per_image_duration=4, fps=FPS, music_path=None):
    """Compilation reel: each image gets its own zoomed segment, concatenated
    into one video, with a single music track laid over the full thing."""
    if music_path is None:
        music_path, _ = pick_track()
    music_path = str(music_path)
    frames = per_image_duration * fps
    total_duration = per_image_duration * len(image_paths)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        clip_paths = []

        for i, img in enumerate(image_paths):
            clip_path = tmp / f"clip_{i}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(img),
                "-vf",
                f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.15)':d={frames}:s=1080x1920:fps={fps}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-t", str(per_image_duration),
                "-an",
                str(clip_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg (clip {i}) failed:\n{result.stderr[-2000:]}")
            clip_paths.append(clip_path)

        concat_list = tmp / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in clip_paths))

        concatenated = tmp / "concatenated.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy",
            str(concatenated),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg (concat) failed:\n{result.stderr[-2000:]}")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(concatenated),
            "-i", music_path,
            "-map", "0:v", "-map", "1:a",
            "-af", f"atrim=0:{total_duration},afade=t=out:st={max(total_duration - 1.2, 0)}:d=1.2,volume=0.7",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg (mux audio) failed:\n{result.stderr[-2000:]}")

    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Animate a static card into a short Reel video")
    parser.add_argument("--image", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--duration", type=int, default=DURATION)
    args = parser.parse_args()

    make_reel(args.image, args.out, duration=args.duration)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
