import httpx
import respx

from scrapers.base import SCRAPERAPI_URL, get


@respx.mock
def test_proxy_request_uses_https_and_encodes_target(monkeypatch):
    monkeypatch.setenv("SCRAPERAPI_KEY", "test-key")
    route = respx.get(SCRAPERAPI_URL).mock(return_value=httpx.Response(200, text="ok"))
    target = "https://slobodnadalmacija.hr/tag/vis?page=2&sort=new"

    get(target, use_proxy=True)

    request = route.calls.last.request
    assert request.url.scheme == "https"
    assert request.url.params["api_key"] == "test-key"
    # The target's own query string must survive as a single encoded param.
    assert request.url.params["url"] == target


@respx.mock
def test_proxy_skipped_without_key(monkeypatch):
    monkeypatch.delenv("SCRAPERAPI_KEY", raising=False)
    target = "https://slobodnadalmacija.hr/tag/vis"
    route = respx.get(target).mock(return_value=httpx.Response(200, text="ok"))

    get(target, use_proxy=True)

    assert route.called
