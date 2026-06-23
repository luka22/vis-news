import os
import httpx
from core.storage import Article

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "hr,en-US;q=0.9,en;q=0.8",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
TIMEOUT = 30


def get(url: str, use_proxy: bool = False) -> httpx.Response:
    """Fetch a URL, optionally routing through ScraperAPI for Cloudflare-blocked sites."""
    scraper_key = os.environ.get("SCRAPERAPI_KEY")
    if use_proxy and scraper_key:
        proxy_url = f"http://api.scraperapi.com?api_key={scraper_key}&url={url}"
        return httpx.get(proxy_url, timeout=TIMEOUT, follow_redirects=True)
    return httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)


class BaseScraper:
    source: str = ""

    def fetch(self) -> list[Article]:
        raise NotImplementedError
