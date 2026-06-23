"""
dalmacijadanas.hr — regional Dalmatia portal with solid Vis island coverage.
Uses the WordPress REST API search endpoint to find Vis-related articles,
then applies keyword filtering to remove false positives (e.g. "VIS" choirs,
"visok" meaning tall, etc.).
"""
import re
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper, get

API_URL = (
    "https://www.dalmacijadanas.hr/wp-json/wp/v2/posts"
    "?search=vis&per_page=30&_fields=id,title,link,date,excerpt"
)

_VIS_ISLAND = [re.compile(p, re.IGNORECASE) for p in [
    r"\botok\s+vis\b",
    r"\bvis(kom|kog|ku|ka|ke|kim|ani|ana)\b",
    r"\bgrad\s+vis\b",
    r"\bna\s+visu\b",
    r"\bs\s+visa\b",
    r"\bvis.?split\b",
    r"\bsplit.?vis\b",
    r"\btrajekt.*vis\b",
    r"\bvis.*trajekt\b",
    r"\bkomiž\w+\b",
    r"\bvis.?prilovo\b",
]]


def _is_about_vis(title: str, excerpt: str) -> bool:
    text = title + " " + excerpt
    return any(pat.search(text) for pat in _VIS_ISLAND)


class DalmacijaDanasScraper(BaseScraper):
    source = "dalmacijadanas.hr"

    def fetch(self) -> list[Article]:
        try:
            resp = get(API_URL)
            resp.raise_for_status()
        except Exception as e:
            print(f"[dalmacijadanas] fetch error: {e}")
            return []

        articles = []
        for post in resp.json():
            title = post.get("title", {}).get("rendered", "").strip()
            url = post.get("link", "")
            if not title or not url:
                continue

            raw_excerpt = post.get("excerpt", {}).get("rendered", "")
            import re as _re
            body = _re.sub(r"<[^>]+>", " ", raw_excerpt).strip()

            if not _is_about_vis(title, body):
                continue

            published = None
            try:
                published = dateparser.parse(post["date"])
            except Exception:
                pass

            articles.append(
                Article(url=url, title=title, source=self.source, published=published, body=body)
            )

        return articles
