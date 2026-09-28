from datetime import datetime, UTC
from core.storage import Article
from core.dedup import dedup_cross_source


def _article(title, source, published=None):
    return Article(url=f"https://{source}/{title}", title=title, source=source, published=published)


def test_near_duplicate_titles_collapse_to_one():
    a = _article("Otok Vis dobio novi vodovod", "gradvis.hr")
    b = _article("Otok Vis dobio je novi vodovod", "index.hr")
    kept = dedup_cross_source([a, b])
    assert len(kept) == 1


def test_near_duplicate_keeps_earlier_published():
    earlier = _article(
        "Otok Vis dobio novi vodovod", "gradvis.hr",
        published=datetime(2026, 1, 1, tzinfo=UTC),
    )
    later = _article(
        "Otok Vis dobio je novi vodovod", "index.hr",
        published=datetime(2026, 1, 5, tzinfo=UTC),
    )
    kept = dedup_cross_source([later, earlier])
    assert len(kept) == 1
    assert kept[0].source == "gradvis.hr"


def test_dissimilar_titles_both_survive():
    a = _article("Otok Vis dobio novi vodovod", "gradvis.hr")
    b = _article("Komiža slavi Filipijadu", "tz-komiza.hr")
    kept = dedup_cross_source([a, b])
    assert len(kept) == 2
