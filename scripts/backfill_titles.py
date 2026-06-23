#!/usr/bin/env python3
"""
One-off migration: translate Croatian titles to English for articles
in seen.db that were processed before title_en was added.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
import anthropic
import os

DB_PATH = Path(__file__).parent.parent / "data" / "seen.db"
BATCH_SIZE = 30
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def fetch_untranslated() -> list[tuple[str, str]]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT url_hash, title FROM seen WHERE title_en IS NULL OR title_en = ''"
    ).fetchall()
    conn.close()
    return rows


def translate_batch(batch: list[tuple[str, str]]) -> dict[str, str]:
    payload = [{"url_hash": h, "title": t} for h, t in batch]
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                "Translate each Croatian article title to English. "
                "Return a JSON array where each element has:\n"
                '- "url_hash": string (copy from input)\n'
                '- "title_en": string (English translation)\n\n'
                "Keep proper nouns (place names, people) unchanged. "
                "Titles:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
            )
        }]
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return {item["url_hash"]: item["title_en"] for item in json.loads(raw)}


def update_db(translations: dict[str, str]) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "UPDATE seen SET title_en = ? WHERE url_hash = ?",
        [(title, hash_) for hash_, title in translations.items()]
    )
    conn.commit()
    conn.close()


def main():
    rows = fetch_untranslated()
    if not rows:
        print("All titles already translated.")
        return

    print(f"{len(rows)} articles need title_en backfill")
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        print(f"  batch {i // BATCH_SIZE + 1}/{-(-len(rows) // BATCH_SIZE)} ({len(batch)} titles)...")
        translations = translate_batch(batch)
        update_db(translations)
        total += len(translations)

    print(f"Done — {total} titles translated.")


if __name__ == "__main__":
    main()
