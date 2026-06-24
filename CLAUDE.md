# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Weekly news aggregator for Vis, a small Croatian island (~3,500 residents). Scrapes 8 sources, deduplicates, summarizes in both Croatian (Split/Dalmatian dialect) and English via Claude API, and renders a static HTML site deployed to GitHub Pages every Monday at 07:00 UTC.

Live site: **https://issa.news**

## Running it

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY (and optionally SCRAPERAPI_KEY)

# Full pipeline
python main.py         # → writes docs/index.html

# Backfill missing English translations in seen.db
python scripts/backfill_titles.py

# Preview output
open docs/index.html
```

`data/seen.db` is gitignored and auto-created on first run. In GitHub Actions it is persisted between runs via `actions/cache`.

## Pipeline (main.py)

1. **Fetch** — all 8 scrapers run in sequence; errors are caught per-scraper and logged to stderr
2. **URL dedup** — `core/storage.filter_new` drops URLs already in `seen.db`
3. **Fuzzy dedup** — `core/dedup.dedup_cross_source` removes near-duplicate titles across sources (SequenceMatcher ≥ 0.75)
4. **Sort** — by `published` date descending
5. **Summarize** — `core/summarize.summarize_articles` calls `claude-sonnet-4-6` in batches of 15
6. **Mark seen** — writes new articles to `seen.db`
7. **Render** — `output/web.render` reads the last 8 days from `seen.db` (not just this run's batch) and writes `docs/index.html` + `docs/sitemap.xml`

## Architecture

### `core/storage.py` — the `Article` dataclass and SQLite store

`Article` is the shared data model passed between all stages. Fields: `url`, `title`, `source`, `published`, `body`, `summary_hr`, `summary_en`, `title_en`, `url_hash` (auto-derived SHA256[:16] of url).

`seen.db` schema: one `seen` table with `url_hash` as primary key. The `get_conn()` function auto-migrates missing columns (`summary_en`, `title_en`) on every connection, so schema changes can be done by adding to that loop.

### `scrapers/` — one file per source

All scrapers inherit `BaseScraper` from `scrapers/base.py` and implement `fetch() -> list[Article]`. Two access patterns:
- **Direct** (`gradvis.py`, `vis_tourism.py`): WordPress REST API at `/wp-json/wp/v2/posts`
- **Direct scrape** (`islandvis.py`, `dalmacijadanas.py`, `tz_komiza.py`, `index_hr.py`): RSS or HTML via httpx + BS4
- **Proxy-required** (`nacional.py`, `slobodnadalmacija.py`): Cloudflare-blocked; routes through ScraperAPI when `SCRAPERAPI_KEY` is set. Without the key these scrapers silently return fewer/no articles.

`base.get()` handles the proxy switch transparently — pass `use_proxy=True` for blocked sites.

### `core/summarize.py` — batched Claude calls

Sends batches of up to 15 articles to Claude as a JSON array, gets back `{url_hash, title_en, summary_hr, summary_en}` for each. The system prompt specifies ikavica/Split dialect for `summary_hr`. Always use `claude-sonnet-4-6`.

### `output/web.py` — rendering

Splits articles into two buckets for the template:
- `articles` (local) — sources in `LOCAL_SOURCES`, capped at 25
- `featured` (regional) — one article per regional source, capped at 3

Also fetches live sidebar data (sea temp, sunrise/sunset, Windy embed) via `core/sidebar.py`.

### `templates/web.html.j2`

Single Jinja2 template. Supports HR/EN language toggle via JS (no server-side routing). Filters `reldate_hr` and `reldate_en` are registered in `output/web.py`.

## Croatian dialect requirement

All `summary_hr` content must be in **Split/Dalmatian dialect (ikavica)**: use *misec, dite, misto, lipo, vrime, ča, pjaca, barka* etc. The system prompt in `core/summarize.py` encodes this — don't weaken it.

## Secrets

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required — Claude summarization |
| `SCRAPERAPI_KEY` | Optional — enables nacional.hr + slobodnadalmacija.hr |

## Adding a new scraper

1. Create `scrapers/mysite.py` inheriting `BaseScraper`, set `source = "mysite.com"`, implement `fetch()`
2. Add to `SCRAPERS` list in `main.py`
3. Add `source` to `LOCAL_SOURCES` or `REGIONAL_SOURCES` in `output/web.py`
