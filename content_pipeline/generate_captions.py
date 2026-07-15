#!/usr/bin/env python3
"""Turn fact dicts into ready-to-paste Facebook captions with hooks + hashtags."""
import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

HOOKS = [
    "Did you know this happened on this exact day?",
    "History fact of the day 👇",
    "Bet you didn't learn this one in school.",
    "On this day, history was made.",
    "Here's a piece of history most people forget.",
]

TRENDING_HOOKS = [
    "Did you know this?",
    "Interesting fact of the day 👇",
    "Bet you didn't know this one.",
    "TIL (today I learned) this, and now you did too.",
    "Here's something most people don't know.",
]

QUESTIONS = [
    "Did you already know this one? Let me know below!",
    "Wild, right? Tag someone who loves history.",
    "How many of these facts did you already know?",
    "Save this for your next trivia night.",
    "What's a history fact YOU know that would surprise us?",
]

TRENDING_QUESTIONS = [
    "Did you already know this one? Let me know below!",
    "Wild, right? Tag someone who'd find this interesting.",
    "Save this for your next trivia night.",
    "Mind blown? Same.",
    "What's a fact YOU know that would surprise us?",
]

REGION_HASHTAGS = {
    "USA": ["#USHistory", "#AmericanHistory", "#USA"],
    "UK": ["#UKHistory", "#BritishHistory", "#UnitedKingdom"],
    "Australia": ["#AustralianHistory", "#Australia", "#AussieHistory"],
    "Europe": ["#EuropeanHistory", "#Europe", "#WorldHistory"],
    "World": ["#WorldHistory", "#History"],
    "Trending": ["#InterestingFacts", "#TIL", "#MindBlown"],
}

BASE_HASHTAGS = ["#OnThisDay", "#HistoryFacts", "#DidYouKnow", "#TodayInHistory", "#FactOfTheDay"]
TRENDING_BASE_HASHTAGS = ["#DidYouKnow", "#FactOfTheDay", "#Facts", "#Trivia"]


def build_caption(fact, index):
    is_trending = fact["region"] == "Trending" or not fact.get("year")
    text = fact["text"]

    if is_trending:
        hook = TRENDING_HOOKS[index % len(TRENDING_HOOKS)]
        question = TRENDING_QUESTIONS[index % len(TRENDING_QUESTIONS)]
        hashtags = " ".join(TRENDING_BASE_HASHTAGS + REGION_HASHTAGS.get(fact["region"], []))
        body = f"💡 {text}"
    else:
        hook = HOOKS[index % len(HOOKS)]
        question = QUESTIONS[index % len(QUESTIONS)]
        hashtags = " ".join(BASE_HASHTAGS + REGION_HASHTAGS.get(fact["region"], []))
        body = f"📅 {fact['year']}: {text}"

    caption = (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"{question}\n\n"
        f"{hashtags}"
    )
    return caption


def main():
    parser = argparse.ArgumentParser(description="Generate FB captions from a facts JSON file")
    parser.add_argument("--facts", default=str(BASE_DIR / "facts_today.json"))
    parser.add_argument("--out", default=str(BASE_DIR / "output" / "captions.txt"))
    args = parser.parse_args()

    facts = json.loads(Path(args.facts).read_text())
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    blocks = []
    for i, fact in enumerate(facts, start=1):
        caption = build_caption(fact, i - 1)
        blocks.append(f"--- fact_{i}.png ---\n{caption}\n")

    out_path.write_text("\n".join(blocks))
    print(f"Wrote {len(facts)} captions to {out_path}")


if __name__ == "__main__":
    main()
