import re
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper, get

API_URL = "https://www.vis-tourism.com/wp-json/wp/v2/posts?per_page=20&_fields=id,title,link,date,excerpt"


class VisTourismScraper(BaseScraper):
    source = "vis-tourism.com"

    def fetch(self) -> list[Article]:
        try:
            resp = get(API_URL)
            resp.raise_for_status()
        except Exception as e:
            print(f"[vis-tourism] fetch error: {e}")
            return []

        articles = []
        for post in resp.json():
            title = post.get("title", {}).get("rendered", "").strip()
            url = post.get("link", "")
            if not title or not url:
                continue

            published = None
            try:
                published = dateparser.parse(post["date"])
            except Exception:
                pass

            raw_excerpt = post.get("excerpt", {}).get("rendered", "")
            body = re.sub(r"<[^>]+>", " ", raw_excerpt).strip()

            articles.append(
                Article(url=url, title=title, source=self.source, published=published, body=body)
            )

        return articles
