import json
import os
import anthropic
from .storage import Article

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


_SYSTEM = """Ti si urednik lokalnih viških novina. Za svaki članak pišeš dva sažetka:

1. Hrvatski sažetak (summary_hr): piši na splitskom dijalektu – dalmatinskom govoru.
   Karakteristike: ikavica (misec, dite, misto, lipo, vrime), tipične dalmatinske riječi
   (ča, nona, pjaca, barka, šjor, bonaca, tramuntana), prirodan i topao ton ka da pričaš
   susjedu na pjaci. Nemoj pretjerivat s dijalektom – neka bude čitljivo ali autentično.

2. English summary (summary_en): write in clear, friendly English as a local correspondent
   covering news from Vis island, Croatia. Keep it informative and concise."""

_USER_TEMPLATE = """Write a short summary (2-3 sentences) for each of the following articles from Vis island.
Return a JSON array where each element has:
- "url_hash": string (copy from input)
- "title_en": string (English translation of the original title)
- "summary_hr": string (summary in Split/Dalmatian dialect Croatian)
- "summary_en": string (summary in English)

Articles:
{articles_json}"""

_BATCH_SIZE = 15


def _summarize_batch(batch: list[Article], attempt: int = 1) -> dict[str, dict]:
    payload = [
        {
            "url_hash": a.url_hash,
            "title": a.title,
            "body": a.body[:1000] if a.body else a.title,
            "source": a.source,
        }
        for a in batch
    ]

    message = _get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": _USER_TEMPLATE.format(
                    articles_json=json.dumps(payload, ensure_ascii=False, indent=2)
                ),
            }
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return {
            item["url_hash"]: {
                "title_en":   item.get("title_en", ""),
                "summary_hr": item.get("summary_hr", ""),
                "summary_en": item.get("summary_en", ""),
            }
            for item in json.loads(raw)
        }
    except (json.JSONDecodeError, KeyError) as e:
        if attempt < 3:
            print(f"[summarize] JSON parse error (attempt {attempt}), retrying: {e}")
            return _summarize_batch(batch, attempt + 1)
        print(f"[summarize] batch failed after 3 attempts, skipping: {e}")
        return {}


def summarize_articles(articles: list[Article]) -> list[Article]:
    if not articles:
        return articles

    summaries: dict[str, dict] = {}
    for i in range(0, len(articles), _BATCH_SIZE):
        batch = articles[i : i + _BATCH_SIZE]
        print(f"[summarize] batch {i // _BATCH_SIZE + 1}/{-(-len(articles) // _BATCH_SIZE)} ({len(batch)} articles)")
        summaries.update(_summarize_batch(batch))

    for article in articles:
        s = summaries.get(article.url_hash, {})
        article.title_en   = s.get("title_en", "")
        article.summary_hr = s.get("summary_hr", "")
        article.summary_en = s.get("summary_en", "")

    return articles
