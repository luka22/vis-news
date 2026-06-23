from datetime import datetime, UTC
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from core.storage import Article
from core.sidebar import fetch_all as fetch_sidebar

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DOCS_DIR = Path(__file__).parent.parent / "docs"
SITE_URL = "https://issa.news"


def _write_sitemap(generated_at: datetime) -> None:
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{generated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    (DOCS_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def render(articles: list[Article], generated_at: datetime | None = None) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    now = generated_at or datetime.now(UTC)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    tmpl = env.get_template("web.html.j2")
    sidebar = fetch_sidebar()
    html = tmpl.render(
        articles=articles,
        generated_at=now,
        sidebar=sidebar,
        site_url=SITE_URL,
    )
    out = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    _write_sitemap(now)
    print(f"[web] wrote {out} ({len(articles)} articles)")
    return out
