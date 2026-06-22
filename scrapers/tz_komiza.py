from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from core.storage import Article
from .base import BaseScraper, get

BASE_URL = "https://www.tz-komiza.hr"
EVENTS_URL = f"{BASE_URL}/dogadanja"


class TzKomizaScraper(BaseScraper):
    source = "tz-komiza.hr"

    def fetch(self) -> list[Article]:
        try:
            resp = get(EVENTS_URL)
            resp.raise_for_status()
        except Exception as e:
            print(f"[tz-komiza] fetch error: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        articles = []

        for a_tag in soup.select("a[href]"):
            href = a_tag.get("href", "")
            if "/dogadanja/" not in href or href.rstrip("/") == EVENTS_URL.rstrip("/"):
                continue

            title = a_tag.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            url = href if href.startswith("http") else BASE_URL + href

            # date sometimes embedded in the link text or a sibling
            published = None
            parent = a_tag.find_parent()
            if parent:
                text = parent.get_text(" ", strip=True)
                # look for date pattern like "19.6.26" or "19.6.2026"
                import re
                m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", text)
                if m:
                    try:
                        published = dateparser.parse(m.group(0))
                    except Exception:
                        pass

            articles.append(
                Article(url=url, title=title, source=self.source, published=published)
            )

        # deduplicate by URL (same event linked multiple times on page)
        seen_urls: set[str] = set()
        unique = []
        for a in articles:
            if a.url not in seen_urls:
                seen_urls.add(a.url)
                unique.append(a)

        return unique[:20]
