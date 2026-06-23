import sqlite3
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "seen.db"


@dataclass
class Article:
    url: str
    title: str
    source: str
    published: datetime | None = None
    body: str = ""
    summary_hr: str = ""
    summary_en: str = ""
    title_en: str = ""
    url_hash: str = field(init=False)

    def __post_init__(self):
        self.url_hash = hashlib.sha256(self.url.encode()).hexdigest()[:16]


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen (
            url_hash TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            published TEXT,
            summary_hr TEXT,
            summary_en TEXT,
            title_en TEXT,
            fetched_at TEXT NOT NULL
        )
    """)
    for col in ("summary_en", "title_en"):
        try:
            conn.execute(f"ALTER TABLE seen ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()
    return conn


def get_recent(days: int = 8) -> list[Article]:
    """Return articles fetched within the last N days, sorted by published date desc."""
    from datetime import timedelta
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM seen WHERE fetched_at >= ?",
        (cutoff,),
    ).fetchall()
    conn.close()

    articles = []
    for row in rows:
        a = Article(url=row["url"], title=row["title"], source=row["source"])
        a.summary_hr = row["summary_hr"] or ""
        a.summary_en = row["summary_en"] or ""
        a.title_en = row["title_en"] or ""
        if row["published"]:
            try:
                from dateutil import parser as dp
                a.published = dp.parse(row["published"])
            except Exception:
                pass
        articles.append(a)

    _epoch = datetime.min.replace(tzinfo=UTC)

    def _sort_key(a: Article):
        dt = a.published or _epoch
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    articles.sort(key=_sort_key, reverse=True)
    return articles


def filter_new(articles: list[Article]) -> list[Article]:
    conn = get_conn()
    hashes = {row["url_hash"] for row in conn.execute("SELECT url_hash FROM seen")}
    conn.close()
    return [a for a in articles if a.url_hash not in hashes]


def mark_seen(articles: list[Article]) -> None:
    conn = get_conn()
    now = datetime.now(UTC).isoformat()
    conn.executemany(
        "INSERT OR IGNORE INTO seen VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (
                a.url_hash,
                a.url,
                a.title,
                a.source,
                a.published.isoformat() if a.published else None,
                a.summary_hr,
                a.summary_en,
                a.title_en,
                now,
            )
            for a in articles
        ],
    )
    conn.commit()
    conn.close()
