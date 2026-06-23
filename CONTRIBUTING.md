# Contributing to vis-news

This document covers commit style, coding conventions, and how to submit
changes. It is inspired by the Linux kernel's
[submitting-patches](https://docs.kernel.org/process/submitting-patches.html)
process — terse, precise, and opinionated.

---

## Commit messages

A commit message consists of a **subject line**, a blank line, and a
**body**. Both matter.

### Subject line

Format: `subsystem: short description`

```
scrapers: fix nacional.hr selector after site redesign
core: prevent fuzzy dedup from collapsing distinct stories
ci: cache seen.db between workflow runs
```

Rules:

- Use the imperative mood — "fix bug", not "fixed bug" or "fixes bug"
- Maximum 72 characters
- No trailing period
- Prefix with the affected subsystem (see list below)
- Be specific — "fix scraper" tells nobody anything

**Subsystems:**

| Prefix | Covers |
|---|---|
| `scrapers:` | Any file under `scrapers/` |
| `core:` | `core/storage.py`, `core/dedup.py`, `core/summarize.py`, `core/sidebar.py` |
| `output:` | `output/web.py` |
| `template:` | `templates/web.html.j2` |
| `ci:` | `.github/workflows/` |
| `docs:` | `README.md`, `CONTRIBUTING.md` |

### Body

The body answers **why**, not what. The diff already shows what changed.

```
scrapers: add ScraperAPI fallback for Cloudflare-blocked sites

Nacional.hr and slobodnadalmacija.hr return 403 from GitHub Actions
runners. Both sites use Cloudflare, which flags AWS/Azure datacenter
IP ranges regardless of User-Agent.

Route these scrapers through ScraperAPI when SCRAPERAPI_KEY is set.
Falls back to a direct request locally where the key is absent, so
local development requires no proxy account.

The free ScraperAPI tier allows 1,000 requests/month. This pipeline
uses approximately 4.
```

Rules:

- Wrap at 72 characters
- Explain the problem first, then the solution
- Do not describe what the code does — describe why it does it
- One commit solves one problem. If you are tempted to write "and" in
  the subject line, split it into two commits

### Trailers

Use `Fixes:` when a commit corrects a specific prior commit:

```
Fixes: a3f92c1 ("scrapers: switch nacional.hr to .item selector")
```

Use `Signed-off-by:` to certify that you wrote the code and have the
right to submit it under the project licence
([DCO](https://developercertificate.org/)):

```
Signed-off-by: Your Name <your@email.com>
```

---

## Coding style

### General

- **Python 3.12+**. Use modern syntax: `X | Y` union types, `match`,
  walrus operator where genuinely clearer.
- **PEP 8** for naming and whitespace, with one exception: line length
  is 88 characters (Black's default), not 79.
- No commented-out code. If it is wrong, delete it. Git remembers.
- No speculative abstractions. Three similar lines is better than a
  premature helper function.

### Comments

Write a comment only when the *why* is not obvious from the code:

```python
# Cloudflare blocks GitHub Actions datacenter IPs regardless of User-Agent.
# Route through ScraperAPI when the key is present.
resp = get(url, use_proxy=True)
```

Do not write comments that restate the code:

```python
# BAD: get the response
resp = get(url)
```

### Functions

Keep functions short. If a function does not fit on one screen, it is
probably doing too much. Name functions after what they return, not how
they work.

### Error handling

Scrapers catch their own exceptions and return an empty list. The
pipeline continues if one source fails — never let one broken site
take down the whole run.

Only validate at system boundaries (user input, external HTTP
responses). Do not defensively check internal data you control.

---

## Submitting changes

1. **One patch, one purpose.** Do not mix a bug fix with a new feature.

2. **Test locally before pushing:**
   ```bash
   python main.py
   open docs/index.html
   ```

3. **Write the commit message before you write the code** if it helps
   you stay focused on a single, describable change.

4. **Push to a branch**, open a pull request, describe what problem it
   solves and why this approach was chosen over alternatives.

---

## Adding a new scraper

1. Create `scrapers/yoursite.py` inheriting from `BaseScraper`
2. Implement `fetch(self) -> list[Article]`
3. Handle exceptions — return `[]` on failure, never raise
4. Add `use_proxy=True` to the `get()` call if the site uses Cloudflare
5. Register in `main.py` `SCRAPERS` list
6. Test: confirm it returns articles locally before committing

```python
from scrapers.base import BaseScraper, get
from core.storage import Article

class YourSiteScraper(BaseScraper):
    source = "yoursite.hr"

    def fetch(self) -> list[Article]:
        try:
            resp = get("https://yoursite.hr/news/", use_proxy=False)
            resp.raise_for_status()
        except Exception as e:
            print(f"[yoursite] fetch error: {e}")
            return []

        # parse and return
        ...
```
