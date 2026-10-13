#!/usr/bin/env python3
"""
Backfill English translations for articles in seen.db missing
title_en or summary_en — runs before main.py on every deploy.
On subsequent runs with nothing to backfill, exits immediately.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from core.summarize import create_message, reply_text

DB_PATH = Path(__file__).parent.parent / "data" / "seen.db"
BATCH_SIZE = 20

_SYSTEM = """You are a translator. For each article, return English translations.
Keep proper nouns (place names like Vis, Komiža, Split; people's names) unchanged."""

_FIELDS = ["url_hash", "title_en", "summary_en"]
_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {f: {"type": "string"} for f in _FIELDS},
                "required": _FIELDS,
                "additionalProperties": False,
            },
        }
    },
    "required": ["articles"],
    "additionalProperties": False,
}


def fetch_incomplete() -> list[tuple[str, str, str]]:
    """Return (url_hash, title, summary_hr) for rows missing title_en or summary_en.

    A missing summary_en only counts when there's a summary_hr to translate —
    otherwise the translation comes back empty and the row would be re-sent to
    Claude on every run.
    """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT url_hash, title, COALESCE(summary_hr, '')
        FROM seen
        WHERE (title_en IS NULL OR title_en = '')
           OR ((summary_en IS NULL OR summary_en = '')
               AND COALESCE(summary_hr, '') != '')
    """).fetchall()
    conn.close()
    return rows


def translate_batch(batch: list[tuple[str, str, str]]) -> dict[str, dict]:
    payload = [
        {"url_hash": h, "title": t, "summary_hr": s}
        for h, t, s in batch
    ]
    msg = create_message(
        system=_SYSTEM,
        content=(
            "Translate each article's title and summary to English.\n"
            'Return one entry in "articles" per input article, each with:\n'
            '- "url_hash": string (copy from input)\n'
            '- "title_en": string (English title)\n'
            '- "summary_en": string (English summary, 2-3 sentences; '
            'empty string if summary_hr is empty)\n\n'
            "Articles:\n" +
            json.dumps(payload, ensure_ascii=False, indent=2)
        ),
        schema=_SCHEMA,
    )
    return {
        item["url_hash"]: {
            "title_en":   item.get("title_en", ""),
            "summary_en": item.get("summary_en", ""),
        }
        for item in json.loads(reply_text(msg))["articles"]
    }


def update_db(translations: dict[str, dict]) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "UPDATE seen SET title_en = ?, summary_en = ? WHERE url_hash = ?",
        [
            (v["title_en"], v["summary_en"], h)
            for h, v in translations.items()
        ]
    )
    conn.commit()
    conn.close()


def main():
    rows = fetch_incomplete()
    if not rows:
        print("[backfill] Nothing to backfill.")
        return

    print(f"[backfill] {len(rows)} articles need title_en / summary_en")
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        print(f"[backfill] batch {i // BATCH_SIZE + 1}/{-(-len(rows) // BATCH_SIZE)} ({len(batch)} articles)...")
        translations = translate_batch(batch)
        update_db(translations)
        total += len(translations)

    print(f"[backfill] Done — {total} articles translated.")


if __name__ == "__main__":
    main()
