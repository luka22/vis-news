from difflib import SequenceMatcher
from .storage import Article

TITLE_SIMILARITY_THRESHOLD = 0.75


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def dedup_cross_source(articles: list[Article]) -> list[Article]:
    """Remove near-duplicate titles across sources, keeping earliest published."""
    kept: list[Article] = []
    for article in articles:
        for existing in kept:
            if _similarity(article.title, existing.title) >= TITLE_SIMILARITY_THRESHOLD:
                # keep the one with an earlier date, or the existing one if no dates
                if (
                    article.published
                    and existing.published
                    and article.published < existing.published
                ):
                    kept.remove(existing)
                    kept.append(article)
                break
        else:
            kept.append(article)
    return kept
