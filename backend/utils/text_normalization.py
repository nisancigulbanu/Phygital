from __future__ import annotations

import unicodedata


MOJIBAKE_REPLACEMENTS = {
    "Ã¼": "ü",
    "Ã¶": "ö",
    "Ã§": "ç",
    "Ä±": "ı",
    "Ä°": "İ",
    "ÅŸ": "ş",
    "Åž": "Ş",
    "ÄŸ": "ğ",
    "Äž": "Ğ",
    "Â°": "°",
}


def repair_mojibake(text: str) -> str:
    repaired = text
    for source, target in MOJIBAKE_REPLACEMENTS.items():
        repaired = repaired.replace(source, target)
    return repaired


def normalize_ascii(text: str) -> str:
    repaired = repair_mojibake(text)
    return unicodedata.normalize("NFKD", repaired).encode("ascii", "ignore").decode("ascii").lower()
