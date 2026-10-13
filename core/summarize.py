import json
import os
import sys
import anthropic
from .storage import Article

MODEL = "claude-opus-5"

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
Return one entry in "articles" per input article, each with:
- "url_hash": string (copy from input)
- "title_en": string (English translation of the original title)
- "summary_hr": string (summary in Split/Dalmatian dialect Croatian)
- "summary_en": string (summary in English)

Articles:
{articles_json}"""

_BATCH_SIZE = 15

# Structured outputs: the API guarantees the reply is JSON matching this schema,
# so a chatty preamble ("Here are the summaries:") can no longer break parsing.
_ARTICLE_FIELDS = ["url_hash", "title_en", "summary_hr", "summary_en"]
_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {f: {"type": "string"} for f in _ARTICLE_FIELDS},
                "required": _ARTICLE_FIELDS,
                "additionalProperties": False,
            },
        }
    },
    "required": ["articles"],
    "additionalProperties": False,
}


def create_message(*, system: str, content: str, schema: dict, max_tokens: int = 16000):
    """Single place every Claude call in the pipeline goes through.

    - output_config.format: the reply is guaranteed to be JSON matching `schema`
    - effort "low": summarizing/translating is routine work; keeps thinking tokens down
    - fallbacks "default": if Opus 5's safety classifiers decline, the API re-runs
      the request on a fallback model server-side instead of returning a refusal
    """
    return _get_client().beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": content}],
    )


def reply_text(message) -> str:
    # Last text block: after a fallback, the model that finished writes the final one.
    return next((b.text for b in reversed(message.content) if b.type == "text"), "")


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

    try:
        message = create_message(
            system=_SYSTEM,
            content=_USER_TEMPLATE.format(
                articles_json=json.dumps(payload, ensure_ascii=False, indent=2)
            ),
            schema=_SCHEMA,
        )
    except anthropic.APIError as e:
        print(f"[summarize] API error, skipping batch: {e}", file=sys.stderr)
        return {}

    raw = reply_text(message)

    try:
        return {
            item["url_hash"]: {
                "title_en":   item.get("title_en", ""),
                "summary_hr": item.get("summary_hr", ""),
                "summary_en": item.get("summary_en", ""),
            }
            for item in json.loads(raw)["articles"]
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Log enough to diagnose: a max_tokens/refusal stop truncates the JSON.
        detail = f"{e} (stop_reason={message.stop_reason}, reply starts {raw[:200]!r})"
        if attempt < 3:
            print(f"[summarize] JSON parse error (attempt {attempt}), retrying: {detail}")
            return _summarize_batch(batch, attempt + 1)
        print(f"[summarize] batch failed after 3 attempts, skipping: {detail}")
        return {}


def summarize_articles(articles: list[Article]) -> list[Article]:
    """Summarize articles, returning only those that got a summary.

    Articles whose batch failed are dropped so the caller doesn't mark them
    seen with empty summaries — they'll be retried on the next run.
    """
    if not articles:
        return articles

    summaries: dict[str, dict] = {}
    for i in range(0, len(articles), _BATCH_SIZE):
        batch = articles[i : i + _BATCH_SIZE]
        print(f"[summarize] batch {i // _BATCH_SIZE + 1}/{-(-len(articles) // _BATCH_SIZE)} ({len(batch)} articles)")
        summaries.update(_summarize_batch(batch))

    summarized = []
    for article in articles:
        s = summaries.get(article.url_hash)
        if s is None:
            continue
        article.title_en   = s["title_en"]
        article.summary_hr = s["summary_hr"]
        article.summary_en = s["summary_en"]
        summarized.append(article)

    return summarized
