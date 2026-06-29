from bs4 import BeautifulSoup
from core.storage import Article
from .base import BaseScraper, get

BASE_URL = "https://slobodnadalmacija.hr"
TAG_URLS = [
    f"{BASE_URL}/tag/otok-vis",
    f"{BASE_URL}/tag/vis",
    f"{BASE_URL}/tag/komiza",
]


class SlobodnaDalmacijaScraper(BaseScraper):
    source = "slobodnadalmacija.hr"

    def fetch(self) -> list[Article]:
        seen_urls: set[str] = set()
        articles = []

        for tag_url in TAG_URLS:
            try:
                resp = get(tag_url, use_proxy=True)
                resp.raise_for_status()
            except Exception as e:
                print(f"[slobodnadalmacija] fetch error ({tag_url}): {e}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            for card in soup.select("article")[:20]:
                a_tag = card.select_one("a.card__article-link")
                if not a_tag:
                    continue

                title = a_tag.get("title", "").strip()
                href = a_tag.get("href", "")
                if not title or not href:
                    continue
                url = href if href.startswith("http") else BASE_URL + href

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                articles.append(
                    Article(url=url, title=title, source=self.source)
                )

        return articles
