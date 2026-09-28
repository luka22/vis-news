from pathlib import Path

import httpx

import scrapers.slobodnadalmacija as slobodnadalmacija
from scrapers.slobodnadalmacija import SlobodnaDalmacijaScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "slobodnadalmacija_tag.html"


def test_slobodnadalmacija_parses_article_cards(monkeypatch):
    html = FIXTURE.read_text()
    monkeypatch.setattr(
        slobodnadalmacija,
        "get",
        lambda url, **kwargs: httpx.Response(200, text=html, request=httpx.Request("GET", url)),
    )

    articles = SlobodnaDalmacijaScraper().fetch()

    assert len(articles) == 2
    assert articles[0].title == "Otok Vis dobio novi vodovod"
    assert articles[0].url == "https://slobodnadalmacija.hr/dalmacija/otok-vis-vodovod"
    assert articles[1].url == "https://slobodnadalmacija.hr/dalmacija/ljetni-festival-komiza"


def test_slobodnadalmacija_returns_empty_list_on_error(monkeypatch):
    def _raise(url, **kwargs):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(slobodnadalmacija, "get", _raise)

    articles = SlobodnaDalmacijaScraper().fetch()

    assert articles == []
