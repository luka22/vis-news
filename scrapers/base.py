import httpx
from core.storage import Article

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VisNewsBot/1.0; +https://github.com/lukaleskur/vis-news)"
}
TIMEOUT = 20


def get(url: str) -> httpx.Response:
    return httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)


class BaseScraper:
    source: str = ""

    def fetch(self) -> list[Article]:
        raise NotImplementedError
