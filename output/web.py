from datetime import datetime, UTC
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from core.storage import Article
from core.sidebar import fetch_all as fetch_sidebar

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DOCS_DIR = Path(__file__).parent.parent / "docs"
SITE_URL = "https://issa.news"

LOCAL_SOURCES = {
    "gradvis.hr",
    "vis-tourism.com",
    "islandvis.blogspot.com",
    "tz-komiza.hr",
    "dalmacijadanas.hr",
}
REGIONAL_SOURCES = {
    "slobodnadalmacija.hr",
    "nacional.hr",
    "index.hr",
    "morski.hr",
    "tportal.hr",
    "jutarnji.hr",
    "hrt.hr",
    "n1info.hr",
}


def _write_sitemap(generated_at: datetime) -> None:
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{generated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    (DOCS_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def _fmt_date(dt, lang: str = "hr") -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    if lang == "hr":
        return dt.strftime("%-d. %-m. %Y.")
    else:
        return dt.strftime("%-d %b %Y")


def render(articles: list[Article], generated_at: datetime | None = None) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    now = generated_at or datetime.now(UTC)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    env.filters["reldate_hr"] = lambda dt: _fmt_date(dt, "hr")
    env.filters["reldate_en"] = lambda dt: _fmt_date(dt, "en")
    tmpl = env.get_template("web.html.j2")
    sidebar = fetch_sidebar()
    local     = articles[:50]
    # one article per regional source, most recently fetched first
    seen_sources: set[str] = set()
    regional = []
    for a in articles:
        if a.source in REGIONAL_SOURCES and a.source not in seen_sources:
            regional.append(a)
            seen_sources.add(a.source)
    regional = regional[:4]
    html = tmpl.render(
        articles=local,
        featured=regional,
        article_count=len(local),
        generated_at=now,
        sidebar=sidebar,
        site_url=SITE_URL,
    )
    out = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    _write_sitemap(now)
    print(f"[web] wrote {out} ({len(articles)} articles)")
    return out
