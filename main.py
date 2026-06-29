#!/usr/bin/env python3
"""
vis-news: weekly Croatian island news aggregator
Run manually or via GitHub Actions cron (Monday 07:00 UTC).
"""
import sys
from datetime import datetime, UTC
from dotenv import load_dotenv
load_dotenv()

from scrapers.gradvis import GradVisScraper
from scrapers.islandvis import IslandVisScraper
from scrapers.nacional import NacionalScraper
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
    NacionalScraper(),
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


def main() -> None:
    print(f"[vis-news] starting run at {datetime.now(UTC).isoformat()}")

    # 1. fetch from all sources
    all_articles = []
    for scraper in SCRAPERS:
        try:
            found = scraper.fetch()
            status = f"{len(found)} articles" if found else "0 articles (blocked or empty)"
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
        print("[vis-news] nothing new this week — rendering empty digest")

    # 4. sort by published date descending
    def _sort_key(a):
        dt = a.published or datetime.min.replace(tzinfo=UTC)
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    new_articles.sort(key=_sort_key, reverse=True)

    # 5. summarize via Claude
    new_articles = summarize_articles(new_articles)
    print(f"[summarize] done")

    # 6. mark as seen
    mark_seen(new_articles)

    # 7. render all articles from the last 8 days (not just this run's batch)
    out = render(get_recent(days=3))
    print(f"[vis-news] done → {out}")


if __name__ == "__main__":
    main()
