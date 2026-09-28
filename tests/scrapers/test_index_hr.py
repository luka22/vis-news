from pathlib import Path

import scrapers.index_hr as index_hr
from scrapers.index_hr import IndexHrScraper

FIXTURE = Path(__file__).parent.parent / "fixtures" / "index_hr_feed.xml"


def test_index_hr_filters_to_vis_only(monkeypatch):
    monkeypatch.setattr(index_hr, "RSS_URL", str(FIXTURE))

    articles = IndexHrScraper().fetch()

    assert len(articles) == 1
    assert articles[0].title == "Otok Vis dobio novi vodovod"
    assert articles[0].source == "index.hr"
    assert articles[0].published is not None
