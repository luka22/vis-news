import re
import feedparser
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper

TAG_FEED  = "https://www.morski.hr/tag/vis/rss/"
MAIN_FEED = "https://www.morski.hr/rss/"


class MorskiScraper(BaseScraper):
    source = "morski.hr"

    def fetch(self) -> list[Article]:
        try:
            feed = feedparser.parse(TAG_FEED)
            entries = feed.entries
            if not entries:
                feed = feedparser.parse(MAIN_FEED)
                entries = [
                    e for e in feed.entries
                    if "vis" in e.get("title", "").lower()
                    or "vis" in e.get("summary", "").lower()
                ]
        except Exception as e:
            print(f"[morski] fetch error: {e}")
            return []

        articles = []
        for entry in entries[:20]:
            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()
            if not title or not url:
                continue

            published = None
            if hasattr(entry, "published"):
                try:
                    published = dateparser.parse(entry.published)
                except Exception:
                    pass

            body = ""
            if hasattr(entry, "summary"):
                body = re.sub(r"<[^>]+>", " ", entry.summary).strip()

            articles.append(
                Article(url=url, title=title, source=self.source, published=published, body=body)
            )
        return articles
