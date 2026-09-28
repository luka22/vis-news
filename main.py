#!/usr/bin/env python3
"""
vis-news: daily Croatian island news aggregator
Run manually or via GitHub Actions cron (daily 05:00 UTC).
"""
import argparse
import os
import sys
from datetime import datetime, UTC
from dotenv import load_dotenv
load_dotenv()

from scrapers.gradvis import GradVisScraper
from scrapers.islandvis import IslandVisScraper
from scrapers.index_hr import IndexHrScraper
from scrapers.slobodnadalmacija import SlobodnaDalmacijaScraper
from scrapers.vis_tourism import VisTourismScraper
from scrapers.tz_komiza import TzKomizaScraper
from scrapers.dalmacijadanas import DalmacijaDanasScraper
from scrapers.morski import MorskiScraper
from scrapers.tportal import TportalScraper
from scrapers.jutarnji import JutarnjiScraper
from scrapers.hrt import HrtScraper
from scrapers.n1 import N1Scraper
from core.storage import filter_new, mark_seen, get_recent
from core.dedup import dedup_cross_source
from core.summarize import summarize_articles
from output.web import render

SCRAPERS = [
    GradVisScraper(),
    IslandVisScraper(),
    IndexHrScraper(),
    SlobodnaDalmacijaScraper(),
    VisTourismScraper(),
    TzKomizaScraper(),
    DalmacijaDanasScraper(),
    MorskiScraper(),
    TportalScraper(),
    JutarnjiScraper(),
    HrtScraper(),
    N1Scraper(),
]


def main(dry_run: bool = False) -> int:
    print(f"[vis-news] starting run at {datetime.now(UTC).isoformat()}")
    if dry_run:
        print("[vis-news] DRY RUN — skipping Claude API calls and seen.db writes")

    # 1. fetch from all sources
    all_articles = []
    for scraper in SCRAPERS:
        try:
            found = scraper.fetch()
            status = f"{len(found)} articles" if found else "0 articles"
            print(f"[{scraper.source}] {status}")
            all_articles.extend(found)
        except Exception as e:
            print(f"[{scraper.source}] ERROR: {e}", file=sys.stderr)

    # 2. filter already-seen URLs
    new_articles = filter_new(all_articles)
    print(f"[dedup] {len(all_articles)} total → {len(new_articles)} new (URL filter)")

    # 3. deduplicate cross-source near-duplicates
    new_articles = dedup_cross_source(new_articles)
    print(f"[dedup] {len(new_articles)} after title fuzzy-dedup")

    if not new_articles:
        print("[vis-news] nothing new since last run")

    # 4. sort by published date descending
    def _sort_key(a):
        dt = a.published or datetime.min.replace(tzinfo=UTC)
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    new_articles.sort(key=_sort_key, reverse=True)

    # 5. summarize via Claude (skipped in dry runs — stub instead)
    unsummarized = 0
    if dry_run:
        for a in new_articles:
            a.title_en = a.title
            a.summary_hr = f"[DRY RUN] {a.title}"
            a.summary_en = f"[DRY RUN] {a.title}"
    else:
        summarized = summarize_articles(new_articles)
        unsummarized = len(new_articles) - len(summarized)
        new_articles = summarized
        print(f"[summarize] done")
        if unsummarized:
            print(f"[summarize] {unsummarized} articles failed — not marking seen, will retry next run", file=sys.stderr)

    # 6. mark as seen (skipped in dry runs — never write to seen.db)
    if not dry_run:
        mark_seen(new_articles)

    # 7. render all articles from the last 3 days (not just this run's batch).
    # Dry runs blend in the unwritten new_articles so the preview looks real
    # without touching seen.db.
    recent = get_recent(days=3)
    preview = new_articles + recent if dry_run else recent
    out = render(preview)
    print(f"[vis-news] done → {out}")

    # Site is rendered either way; still fail the run so summarization errors get noticed.
    return 1 if unsummarized else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip Claude API calls and seen.db writes; render a preview only",
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run or os.environ.get("DRY_RUN") == "1"))
