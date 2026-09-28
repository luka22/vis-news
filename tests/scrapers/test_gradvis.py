import json
from pathlib import Path

import httpx
import respx

from scrapers.gradvis import GradVisScraper, API_URL

FIXTURE = Path(__file__).parent.parent / "fixtures" / "gradvis_posts.json"


@respx.mock
def test_gradvis_parses_wordpress_posts():
    posts = json.loads(FIXTURE.read_text())
    respx.get(API_URL).mock(return_value=httpx.Response(200, json=posts))

    articles = GradVisScraper().fetch()

    assert len(articles) == 2
    assert articles[0].title == "Otok Vis dobio novi vodovod"
    assert articles[0].url == "https://www.gradvis.hr/vijesti/otok-vis-dobio-novi-vodovod"
    assert articles[0].source == "gradvis.hr"
    assert "vodovoda" in articles[0].body
    assert articles[0].published is not None


@respx.mock
def test_gradvis_returns_empty_list_on_error():
    respx.get(API_URL).mock(return_value=httpx.Response(500))

    articles = GradVisScraper().fetch()

    assert articles == []
