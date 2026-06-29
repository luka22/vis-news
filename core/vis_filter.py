import re

_VIS_PATTERNS = [
    r"\botok\s+vis\b",
    r"\botoka\s+visa\b",
    r"\bvis(kom|kog|ku|ka|ke|kim|u)\b",  # all declined forms incl. Visu (locative)
    r"\bgrad\s+vis\b",
    r"\bvišan[ai]?\b",                   # Višani (inhabitants)
    r"\bviska\b",
    r"\bkomuna\s+vis\b",
    r"\bkomiž",                           # Komiža — only on Vis island
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _VIS_PATTERNS]


def mentions_vis(text: str) -> bool:
    return any(pat.search(text) for pat in _COMPILED)
