# Viške novosti / Vis Island News

Live at [issa.news](https://issa.news).

Automated weekly news aggregator for [Vis](https://en.wikipedia.org/wiki/Vis), a Croatian island in the Adriatic. Scrapes 7 local and regional sources, summarises articles in both Croatian (Split dialect) and English using Claude AI, and publishes a static website every Monday.

---

## Sources

| Source | Method | Notes |
|---|---|---|
| [gradvis.hr](https://www.gradvis.hr) | WordPress REST API | Official city website |
| [vis-tourism.com](https://www.vis-tourism.com) | WordPress REST API | TZ Vis tourism board |
| [tz-komiza.hr](https://www.tz-komiza.hr) | Scraper | Komiža events |
| [islandvis.blogspot.com](https://islandvis.blogspot.com) | RSS | Local blog |
| [slobodnadalmacija.hr](https://slobodnadalmacija.hr/tag/otok-vis) | Scraper | Regional daily (requires proxy, see setup) |
| [nacional.hr](https://www.nacional.hr/tag/vis/) | Scraper | National portal (requires proxy, see setup) |
| [index.hr](https://www.index.hr/rss) | RSS + keyword filter | National portal |

---

## How it works

```
Every Monday 07:00 UTC
        │
        ▼
1. FETCH      — all 7 scrapers run, collect articles
        │
        ▼
2. DEDUP      — filter already-seen URLs (SQLite), fuzzy-match cross-source duplicates
        │
        ▼
3. SUMMARISE  — Claude generates 2–3 sentence summaries in Split dialect Croatian + English
        │
        ▼
4. STORE      — mark articles as seen in seen.db (persisted between runs)
        │
        ▼
5. RENDER     — Jinja2 renders docs/index.html with all articles from the last 8 days
        │
        ▼
6. DEPLOY     — GitHub Pages publishes the updated static site
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

---

## GitHub Actions deployment

The workflow runs automatically every Monday at 07:00 UTC and deploys to GitHub Pages.

### 1. Enable GitHub Pages

Repo → **Settings → Pages → Source: GitHub Actions**

### 2. Add repository secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to get it | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | ✅ Yes |
| `SCRAPERAPI_KEY` | [scraperapi.com](https://www.scraperapi.com) — free tier covers usage | Optional — enables slobodnadalmacija.hr + nacional.hr in Actions |

> **Note on blocked scrapers:** slobodnadalmacija.hr and nacional.hr use Cloudflare which blocks GitHub Actions' datacenter IPs. Setting `SCRAPERAPI_KEY` routes these through residential proxies. The free ScraperAPI tier (1,000 req/month) is more than sufficient — the workflow uses ~4/month.

### 3. Trigger the first run

**Actions → Weekly Vis News Digest → Run workflow**

Or via CLI:
```bash
gh workflow run digest.yml
```

Your site will be live at `https://your-username.github.io/vis-news/` after the first run (~5–7 minutes).

---

## Project structure

```
vis-news/
├── .github/workflows/digest.yml   # Monday cron + GitHub Pages deploy
├── core/
│   ├── dedup.py                   # URL + fuzzy title deduplication
│   ├── sidebar.py                 # Live sea conditions + sun times
│   ├── storage.py                 # SQLite seen-article tracking
│   └── summarize.py               # Claude API summarisation
├── scrapers/
│   ├── base.py                    # Shared httpx client + optional ScraperAPI proxy
│   ├── gradvis.py                 # gradvis.hr (WordPress API)
│   ├── index_hr.py                # index.hr (RSS + keyword filter)
│   ├── islandvis.py               # islandvis.blogspot.com (RSS)
│   ├── nacional.py                # nacional.hr (scraper, proxy-enabled)
│   ├── slobodnadalmacija.py       # slobodnadalmacija.hr (scraper, proxy-enabled)
│   ├── tz_komiza.py               # tz-komiza.hr (scraper)
│   └── vis_tourism.py             # vis-tourism.com (WordPress API)
├── output/
│   └── web.py                     # Renders docs/index.html
├── templates/
│   └── web.html.j2                # Jinja2 HTML template (HR/EN language toggle)
├── docs/
│   └── index.html                 # Generated output
├── data/                          # gitignored — contains seen.db
├── main.py                        # Pipeline entrypoint
├── requirements.txt
└── .env.example
```

---

## Cost

| Service | Cost |
|---|---|
| Anthropic API (`claude-sonnet-4-6`) | ~$0.05–0.15/week |
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
