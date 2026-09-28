# Viške novosti / Vis Island News

Live at [issa.news](https://issa.news).

Automated daily news aggregator for [Vis](https://en.wikipedia.org/wiki/Vis), a Croatian island in the Adriatic. Scrapes 12 local, regional, and national sources, summarises articles in both Croatian (Split dialect) and English using Claude AI, and publishes a static website every day.

---

## Sources

| Source | Method | Notes |
|---|---|---|
| [gradvis.hr](https://www.gradvis.hr) | WordPress REST API | Official city website |
| [vis-tourism.com](https://www.vis-tourism.com) | WordPress REST API | TZ Vis tourism board |
| [tz-komiza.hr](https://www.tz-komiza.hr) | Scraper | Komiža events |
| [islandvis.blogspot.com](https://islandvis.blogspot.com) | RSS | Local blog |
| [dalmacijadanas.hr](https://www.dalmacijadanas.hr) | WordPress REST API + keyword filter | Regional portal |
| [slobodnadalmacija.hr](https://slobodnadalmacija.hr/tag/otok-vis) | Scraper | Regional daily (requires proxy, see setup) |
| [index.hr](https://www.index.hr/rss) | RSS + keyword filter | National portal |
| [morski.hr](https://www.morski.hr) | RSS (tag feed) | Adriatic/maritime news |
| [tportal.hr](https://www.tportal.hr) | RSS + keyword filter | National portal |
| [jutarnji.hr](https://www.jutarnji.hr) | RSS + keyword filter | National portal |
| [hrt.hr](https://hrt.hr) | RSS + keyword filter | National broadcaster |
| [n1info.hr](https://n1info.hr) | RSS + keyword filter | National portal |

---

## How it works

```
┌───────────────────────── GitHub Actions · daily 05:00 UTC ────────────────────────┐
│                                                                                    │
│   DIRECT ACCESS                          CLOUDFLARE BLOCKED                       │
│   ┌──────────────────────┐               ┌──────────────────────┐                 │
│   │ gradvis.hr           │               │ slobodnadalmacija.hr │                 │
│   │ vis-tourism.com      │               └──────────┬───────────┘                 │
│   │ islandvis.blogspot   │                          │ blocked by                  │
│   │ tz-komiza.hr         │                          │ Cloudflare                  │
│   │ dalmacijadanas.hr    │               ┌──────────▼───────────┐                 │
│   │ index.hr (RSS)       │               │  ScraperAPI          │                 │
│   │ morski/tportal/      │               │  residential proxy   │                 │
│   │ jutarnji/hrt/n1      │               └──────────┬───────────┘                 │
│   │ (RSS + keyword)      │                          │                             │
│   └──────────┬───────────┘                          │                             │
│              │                                      │                             │
│              └──────────────────┬───────────────────┘                             │
│                                 │                                                 │
│                                 ▼                                                 │
│                    ┌────────────────────────┐   ┌─────────────────────────┐      │
│                    │         DEDUP          │◄──│ seen.db  (SQLite)       │      │
│                    │  URL hash · fuzzy title│   │ cached between runs     │      │
│                    └────────────┬───────────┘   └─────────────────────────┘      │
│                                 │                                                 │
│                                 ▼                                                 │
│                    ┌────────────────────────┐                                     │
│                    │       SUMMARISE        │  claude-sonnet-4-6                  │
│                    │  Croatian Split dialect│                                     │
│                    │  + English             │                                     │
│                    └────────────┬───────────┘                                     │
│                                 │                                                 │
│                                 ▼                                                 │
│                    ┌────────────────────────┐   ┌─────────────────────────┐      │
│                    │         RENDER         │◄──│ Live sidebar            │      │
│                    │  Jinja2 → index.html   │   │ sea temp · sun · Windy  │      │
│                    └────────────┬───────────┘   └─────────────────────────┘      │
│                                 │                                                 │
└─────────────────────────────────┼─────────────────────────────────────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │    GitHub Pages      │
                       │    visnews.hr (TBD)  │
                       └──────────────────────┘
```

---

## Local setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/vis-news.git
cd vis-news
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add your Anthropic API key

Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys.

```bash
cp .env.example .env
# edit .env:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run

```bash
python main.py
```

Output is written to `docs/index.html`:

```bash
open docs/index.html        # macOS
xdg-open docs/index.html    # Linux
```

To iterate without spending API credits, use dry-run mode — real scrapers run, but
Claude calls and `seen.db` writes are skipped:

```bash
python main.py --dry-run
```

### 4. Run the test suite

```bash
pip install -r requirements-dev.txt
pytest
```

No network access or API keys needed — see `CLAUDE.md` for what's covered.

---

## GitHub Actions deployment

The workflow runs automatically every day at 05:00 UTC and deploys to GitHub Pages.
A separate `test.yml` workflow runs `pytest` and a dry-run pipeline on every pull
request (no secrets required).

### 1. Enable GitHub Pages

Repo → **Settings → Pages → Source: GitHub Actions**

### 2. Add repository secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to get it | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | ✅ Yes |
| `SCRAPERAPI_KEY` | [scraperapi.com](https://www.scraperapi.com) — free tier covers usage | Optional — enables slobodnadalmacija.hr in Actions |

> **Note on blocked scrapers:** slobodnadalmacija.hr uses Cloudflare, which blocks GitHub Actions' datacenter IPs. Setting `SCRAPERAPI_KEY` routes it through a residential proxy. The free ScraperAPI tier (1,000 req/month) is more than sufficient — the workflow uses ~4/month.

### 3. Trigger the first run

**Actions → Daily Vis News Digest → Run workflow**

Or via CLI:
```bash
gh workflow run digest.yml
```

Your site will be live at `https://your-username.github.io/vis-news/` after the first run (~5–7 minutes).

---

## Project structure

```
vis-news/
├── .github/workflows/
│   ├── digest.yml                 # Daily cron + GitHub Pages deploy
│   ├── test.yml                   # PR: pytest + dry-run pipeline, no secrets
│   └── zizmor.yml                 # Security lint for workflow files
├── core/
│   ├── dedup.py                   # URL + fuzzy title deduplication
│   ├── sidebar.py                 # Live sea conditions + sun times
│   ├── storage.py                 # SQLite seen-article tracking
│   ├── summarize.py               # Claude API summarisation
│   └── vis_filter.py              # Vis-island keyword filter for regional RSS feeds
├── scrapers/
│   ├── base.py                    # Shared httpx client + optional ScraperAPI proxy
│   ├── gradvis.py                 # gradvis.hr (WordPress API)
│   ├── vis_tourism.py             # vis-tourism.com (WordPress API)
│   ├── islandvis.py               # islandvis.blogspot.com (RSS)
│   ├── dalmacijadanas.py          # dalmacijadanas.hr (WordPress API + keyword filter)
│   ├── tz_komiza.py               # tz-komiza.hr (scraper)
│   ├── slobodnadalmacija.py       # slobodnadalmacija.hr (scraper, proxy-enabled)
│   ├── index_hr.py                # index.hr (RSS + keyword filter)
│   ├── morski.py                  # morski.hr (RSS tag feed)
│   ├── tportal.py                 # tportal.hr (RSS + keyword filter)
│   ├── jutarnji.py                # jutarnji.hr (RSS + keyword filter)
│   ├── hrt.py                     # hrt.hr (RSS + keyword filter)
│   └── n1.py                      # n1info.hr (RSS + keyword filter)
├── output/
│   └── web.py                     # Renders docs/index.html
├── templates/
│   └── web.html.j2                # Jinja2 HTML template (HR/EN language toggle)
├── scripts/
│   └── backfill_titles.py         # Backfills missing English translations
├── tests/                         # pytest suite — no network or API cost
├── docs/
│   └── index.html                 # Generated output
├── data/                          # gitignored — contains seen.db
├── main.py                        # Pipeline entrypoint (supports --dry-run)
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

---

## Cost

| Service | Cost |
|---|---|
| Anthropic API (`claude-sonnet-4-6`) | Small per-article cost, batched; runs daily |
| ScraperAPI | Free (1,000 req/month, ~4 used) |
| GitHub Actions | Free |
| GitHub Pages | Free |
| **Total** | **< $1/month** |

---

## Tech stack

Python · httpx · BeautifulSoup4 · feedparser · Anthropic API · Jinja2 · SQLite · GitHub Actions · GitHub Pages

---

## License

MIT
