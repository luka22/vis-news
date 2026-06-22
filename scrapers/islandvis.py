import feedparser
from datetime import datetime
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper

RSS_URL = "https://islandvis.blogspot.com/feeds/posts/default?alt=rss"


class IslandVisScraper(BaseScraper):
    source = "islandvis.blogspot.com"

    def fetch(self) -> list[Article]:
        feed = feedparser.parse(RSS_URL)
        articles = []
        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, "published"):
                try:
                    published = dateparser.parse(entry.published)
                except Exception:
                    pass

            body = ""
            if hasattr(entry, "summary"):
                # strip HTML tags crudely — bs4 not worth importing just for this
                import re
                body = re.sub(r"<[^>]+>", " ", entry.summary).strip()

            articles.append(
                Article(
                    url=entry.link,
                    title=entry.title,
                    source=self.source,
                    published=published,
                    body=body,
                )
            )
        return articles
