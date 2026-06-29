import re
import feedparser
from dateutil import parser as dateparser
from core.storage import Article
from core.vis_filter import mentions_vis
from .base import BaseScraper

RSS_URL = "https://n1info.hr/feed/"


class N1Scraper(BaseScraper):
    source = "n1info.hr"

    def fetch(self) -> list[Article]:
        try:
            feed = feedparser.parse(RSS_URL)
        except Exception as e:
            print(f"[n1info.hr] fetch error: {e}")
            return []

        articles = []
        for entry in feed.entries:
            combined = entry.get("title", "") + " " + entry.get("summary", "")
            if not mentions_vis(combined):
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
