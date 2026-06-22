"""
index.hr tag pages are JavaScript-rendered and can't be scraped statically.
Instead we pull their main RSS feed and filter for articles about Vis island.
"""
import re
import feedparser
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper

RSS_URL = "https://www.index.hr/rss"

# keywords that indicate the article is about Vis island (not just "visok", etc.)
_VIS_PATTERNS = [
    r"\botok\s+vis\b",
    r"\bvis(kom|kog|ku|ka|ke|kim)\b",   # Viskom, Viskog, Visku …
    r"\bgrad\s+vis\b",
    r"\bvišan[ai]?\b",                  # Višani (inhabitants)
    r"\bviska\b",
    r"\bkomuna\s+vis\b",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _VIS_PATTERNS]


def _mentions_vis(text: str) -> bool:
    return any(pat.search(text) for pat in _COMPILED)


class IndexHrScraper(BaseScraper):
    source = "index.hr"

    def fetch(self) -> list[Article]:
        try:
            feed = feedparser.parse(RSS_URL)
        except Exception as e:
            print(f"[index.hr] fetch error: {e}")
            return []

        articles = []
        for entry in feed.entries:
            combined = entry.get("title", "") + " " + entry.get("summary", "")
            if not _mentions_vis(combined):
                continue

            title = entry.get("title", "").strip()
            url = entry.get("link", "")
            if not title or not url:
                continue

            published = None
            if hasattr(entry, "published"):
                try:
                    published = dateparser.parse(entry.published)
                except Exception:
                    pass

            body = re.sub(r"<[^>]+>", " ", entry.get("summary", "")).strip()

            articles.append(
                Article(url=url, title=title, source=self.source, published=published, body=body)
            )

        return articles
