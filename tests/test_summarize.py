import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import core.summarize as summarize
from core.storage import Article


def _fake_message(text: str):
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _article(url_hash_seed: str):
    return Article(url=f"https://gradvis.hr/{url_hash_seed}", title=f"Vijest {url_hash_seed}", source="gradvis.hr")


def test_summarize_articles_parses_response(monkeypatch):
    articles = [_article("a")]
    url_hash = articles[0].url_hash

    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_message(json.dumps([
        {
            "url_hash": url_hash,
            "title_en": "News A",
            "summary_hr": "Sažetak A",
            "summary_en": "Summary A",
        }
    ]))
    monkeypatch.setattr(summarize, "_get_client", lambda: fake_client)

    result = summarize.summarize_articles(articles)

    assert result[0].title_en == "News A"
    assert result[0].summary_hr == "Sažetak A"
    assert result[0].summary_en == "Summary A"
    fake_client.messages.create.assert_called_once()


def test_summarize_batch_retries_on_bad_json_then_succeeds(monkeypatch):
    article = _article("b")
    url_hash = article.url_hash
    good_response = json.dumps([
        {"url_hash": url_hash, "title_en": "News B", "summary_hr": "S", "summary_en": "S"}
    ])

    fake_client = MagicMock()
    fake_client.messages.create.side_effect = [
        _fake_message("not json"),
        _fake_message("still not json"),
        _fake_message(good_response),
    ]
    monkeypatch.setattr(summarize, "_get_client", lambda: fake_client)

    result = summarize._summarize_batch([article])

    assert result[url_hash]["title_en"] == "News B"
    assert fake_client.messages.create.call_count == 3


def test_summarize_batch_gives_up_after_three_failures(monkeypatch):
    article = _article("c")

    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_message("not json")
    monkeypatch.setattr(summarize, "_get_client", lambda: fake_client)

    result = summarize._summarize_batch([article])

    assert result == {}
    assert fake_client.messages.create.call_count == 3


def test_summarize_articles_drops_articles_when_api_errors(monkeypatch):
    import anthropic
    import httpx

    articles = [_article("d")]
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic.APIConnectionError(request=request)
    monkeypatch.setattr(summarize, "_get_client", lambda: fake_client)

    assert summarize.summarize_articles(articles) == []
