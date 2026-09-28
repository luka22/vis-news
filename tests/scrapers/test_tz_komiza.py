from pathlib import Path

import httpx
import respx

from scrapers.tz_komiza import TzKomizaScraper, EVENTS_URL

FIXTURE = Path(__file__).parent.parent / "fixtures" / "tz_komiza_events.html"


@respx.mock
def test_tz_komiza_parses_event_links():
    html = FIXTURE.read_text()
    respx.get(EVENTS_URL).mock(return_value=httpx.Response(200, text=html))

    articles = TzKomizaScraper().fetch()

    titles = {a.title for a in articles}
    assert titles == {"Filipijada 2026", "Koncert na rivi"}
    urls = {a.url for a in articles}
    assert "https://www.tz-komiza.hr/dogadanja/filipijada-2026" in urls
    assert "https://www.tz-komiza.hr/dogadanja/koncert-na-rivi" in urls
    assert all(a.published is not None for a in articles)


@respx.mock
def test_tz_komiza_returns_empty_list_on_error():
    respx.get(EVENTS_URL).mock(return_value=httpx.Response(500))

    articles = TzKomizaScraper().fetch()

    assert articles == []
