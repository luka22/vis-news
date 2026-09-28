from datetime import datetime, UTC
import core.storage as storage
from core.storage import Article, filter_new, mark_seen, get_recent


def test_url_hash_is_derived_and_stable():
    a1 = Article(url="https://gradvis.hr/vijest-1", title="Vijest", source="gradvis.hr")
    a2 = Article(url="https://gradvis.hr/vijest-1", title="Different title", source="gradvis.hr")
    a3 = Article(url="https://gradvis.hr/vijest-2", title="Vijest", source="gradvis.hr")
    assert a1.url_hash == a2.url_hash
    assert a1.url_hash != a3.url_hash


def test_filter_new_mark_seen_get_recent_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "seen.db")

    a = Article(
        url="https://gradvis.hr/vijest-1",
        title="Vijest",
        source="gradvis.hr",
        published=datetime(2026, 1, 1, tzinfo=UTC),
    )
    a.summary_hr = "Sažetak"
    a.summary_en = "Summary"
    a.title_en = "News"

    assert filter_new([a]) == [a]

    mark_seen([a])

    assert filter_new([a]) == []  # now seen, filtered out

    recent = get_recent(days=3)
    assert len(recent) == 1
    assert recent[0].url == a.url
    assert recent[0].summary_hr == "Sažetak"
    assert recent[0].summary_en == "Summary"
    assert recent[0].title_en == "News"


def test_mark_seen_ignores_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "seen.db")

    a = Article(url="https://gradvis.hr/vijest-1", title="Vijest", source="gradvis.hr")
    mark_seen([a])
    mark_seen([a])  # should not raise or duplicate

    recent = get_recent(days=3)
    assert len(recent) == 1
