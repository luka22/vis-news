from datetime import datetime, UTC
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from core.storage import Article
from core.sidebar import fetch_all as fetch_sidebar

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUT_PATH = Path(__file__).parent.parent / "docs" / "index.html"


def render(articles: list[Article], generated_at: datetime | None = None) -> Path:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    tmpl = env.get_template("web.html.j2")
    sidebar = fetch_sidebar()
    html = tmpl.render(
        articles=articles,
        generated_at=generated_at or datetime.now(UTC),
        sidebar=sidebar,
    )
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"[web] wrote {OUT_PATH} ({len(articles)} articles)")
    return OUT_PATH
