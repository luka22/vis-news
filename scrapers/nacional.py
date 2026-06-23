from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper, get

BASE_URL = "https://www.nacional.hr"
TAG_URL = f"{BASE_URL}/tag/vis/"


class NacionalScraper(BaseScraper):
    source = "nacional.hr"

    def fetch(self) -> list[Article]:
        try:
            resp = get(TAG_URL, use_proxy=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"[nacional] fetch error: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        articles = []

        # each .item has a direct <a> wrapper; title is in h5, date in p.text-muted
        for card in soup.select(".item")[:20]:
            a_tag = card.select_one("a[href]")
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if not href:
                continue
            url = href if href.startswith("http") else BASE_URL + href

            h_tag = card.select_one("h5, h4, h3, h2")
            title = h_tag.get_text(strip=True) if h_tag else a_tag.get_text(strip=True)
            if not title:
                continue

            published = None
            time_tag = card.select_one("time")
            if time_tag:
                dt_str = time_tag.get("datetime") or time_tag.get_text(strip=True)
                try:
                    published = dateparser.parse(dt_str)
                except Exception:
                    pass

            body = ""
            excerpt = card.select_one("p:not(.text-muted)")
            if excerpt:
                body = excerpt.get_text(strip=True)

            articles.append(
                Article(url=url, title=title, source=self.source, published=published, body=body)
            )

        return articles
