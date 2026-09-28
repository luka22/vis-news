import importlib.util
from pathlib import Path

import core.storage as storage
from core.storage import Article, mark_seen

_SCRIPT = Path(__file__).parent.parent / "scripts" / "backfill_titles.py"


def _load_backfill(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")  # client is built at import time
    spec = importlib.util.spec_from_file_location("backfill_titles", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _article(slug, title_en="", summary_hr="", summary_en=""):
    a = Article(url=f"https://gradvis.hr/{slug}", title=f"Vijest {slug}", source="gradvis.hr")
    a.title_en, a.summary_hr, a.summary_en = title_en, summary_hr, summary_en
    return a


def test_fetch_incomplete_skips_rows_with_nothing_to_translate(tmp_path, monkeypatch):
    db = tmp_path / "seen.db"
    monkeypatch.setattr(storage, "DB_PATH", db)
    backfill = _load_backfill(monkeypatch)
    monkeypatch.setattr(backfill, "DB_PATH", db)

    complete = _article("complete", title_en="News", summary_hr="Sažetak", summary_en="Summary")
    no_title = _article("no-title", summary_hr="Sažetak", summary_en="Summary")
    no_summary_en = _article("no-summary-en", title_en="News", summary_hr="Sažetak")
    # Translated title but no Croatian summary: summary_en will always come
    # back empty, so this row must not be re-sent on every run.
    no_summary_at_all = _article("no-summary", title_en="News")
    mark_seen([complete, no_title, no_summary_en, no_summary_at_all])

    hashes = {row[0] for row in backfill.fetch_incomplete()}

    assert hashes == {no_title.url_hash, no_summary_en.url_hash}
