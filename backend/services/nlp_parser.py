from __future__ import annotations

import re
from backend.utils.text_normalization import normalize_ascii, repair_mojibake


FABRIC_ALIASES = {
    "cotton": "pamuk",
    "coton": "pamuk",
    "cotone": "pamuk",
    "baumwolle": "pamuk",
    "algodon": "pamuk",
    "pamut": "pamuk",
    "pamuk": "pamuk",
    "polyester": "polyester",
    "poliester": "polyester",
    "polyesteri": "polyester",
    "wool": "yun",
    "lana": "yun",
    "laine": "yun",
    "wolle": "yun",
    "yun": "yun",
    "silk": "ipek",
    "soie": "ipek",
    "seta": "ipek",
    "seide": "ipek",
    "ipek": "ipek",
    "linen": "keten",
    "lin": "keten",
    "lino": "keten",
    "leinen": "keten",
    "keten": "keten",
    "elastane": "elastan",
    "spandex": "elastan",
    "lycra": "elastan",
    "elasthanne": "elastan",
    "elastan": "elastan",
    "viscose": "viskon",
    "rayon": "viskon",
    "viskose": "viskon",
    "viskon": "viskon",
    "viskoz": "viskon",
    "organic cotton": "pamuk",
    "organik pamuk": "pamuk",
    "recycled polyester": "polyester",
    "geri donusturulmus polyester": "polyester",
    "merino wool": "yun",
    "merinos yun": "yun",
    "nylon": "naylon",
    "polyamide": "naylon",
    "polyamid": "naylon",
    "poliamit": "naylon",
    "naylon": "naylon",
    "acrylic": "akrilik",
    "acrylique": "akrilik",
    "acrilico": "akrilik",
    "akrilik": "akrilik",
}

FABRIC_STEMS = {
    "pamuk": "pamuk",
    "cotton": "pamuk",
    "polyester": "polyester",
    "polyamid": "naylon",
    "polyami": "naylon",
    "poliamit": "naylon",
    "poliami": "naylon",
    "polyamide": "naylon",
    "naylon": "naylon",
    "nylon": "naylon",
    "akrilik": "akrilik",
    "acrylic": "akrilik",
    "elastan": "elastan",
    "elastane": "elastan",
    "yun": "yun",
    "wool": "yun",
    "viskon": "viskon",
    "viskoz": "viskon",
    "viscose": "viskon",
    "keten": "keten",
    "linen": "keten",
}

PERCENTAGE_PATTERN = re.compile(r"(\d{1,3})\s*%\s*([a-zA-Z\u00C7-\u00FC]+(?:\s[a-zA-Z\u00C7-\u00FC]+)?)", re.IGNORECASE)
REVERSE_PATTERN = re.compile(r"([a-zA-Z\u00C7-\u00FC]+(?:\s[a-zA-Z\u00C7-\u00FC]+)?)\s*%\s*(\d{1,3})", re.IGNORECASE)
LEADING_PERCENT_PATTERN = re.compile(r"%\s*(\d{1,3})\s*([a-zA-Z\u00C7-\u00FC]+(?:\s[a-zA-Z\u00C7-\u00FC]+)?)", re.IGNORECASE)
ORIGIN_PATTERN = re.compile(r"(?:made\s+in|uretim\s+yeri|fabricado\s+en|fabrique\s+en)\s*:?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", re.IGNORECASE)
CARE_PATTERNS = (
    re.compile(r"(\d{2}\s?°?\s?c)"),
    re.compile(r"(dry clean)"),
    re.compile(r"(low iron)"),
    re.compile(r"(do not bleach)"),
)
BRAND_PATTERN = re.compile(r"\b(zara|hm|mango|lc waikiki|koton|defacto)\b", re.IGNORECASE)
KNOWN_COUNTRIES = (
    "Bangladesh",
    "Turkey",
    "China",
    "Vietnam",
    "Cambodia",
    "India",
    "Italy",
    "Portugal",
    "Germany",
    "France",
    "Japan",
)


def parse_label_text(raw_text: str) -> dict:
    """Parse OCR text into normalized fabric composition and supporting metadata."""
    repaired_text = repair_mojibake(raw_text)
    normalized_text = _normalize(repaired_text)
    composition = _parse_fabric_composition(normalized_text)
    origin_country = _parse_origin(repaired_text)
    care = _parse_care_instructions(normalized_text)
    brand = _parse_brand(repaired_text)

    if not composition:
        return {
            "error": "fabric_not_found",
            "origin_country": origin_country,
            "care_instructions": care,
            "brand": brand,
            "parse_confidence": 0.0,
        }

    total = sum(composition.values())
    confidence = 0.88
    if total != 100:
        confidence = 0.62 if 0 < total <= 120 else 0.35

    return {
        "fabric_composition": composition,
        "origin_country": origin_country,
        "care_instructions": care,
        "brand": brand,
        "parse_confidence": confidence,
    }


def _parse_fabric_composition(text: str) -> dict[str, float]:
    composition: dict[str, float] = {}
    tokens = re.findall(r"%?\d{1,3}%?|[a-zA-Z\u00C7-\u00FC]+", text)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        percentage = _parse_percentage_token(token)
        if percentage is not None:
            words: list[str] = []
            next_index = index + 1
            while next_index < len(tokens) and _parse_percentage_token(tokens[next_index]) is None and len(words) < 3:
                words.append(tokens[next_index])
                next_index += 1
            if words:
                _add_composition_entry(composition, " ".join(words), str(percentage))
                index = next_index
                continue
        else:
            words = [token]
            next_index = index + 1
            while next_index < len(tokens) and _parse_percentage_token(tokens[next_index]) is None and len(words) < 3:
                words.append(tokens[next_index])
                next_index += 1
            if next_index < len(tokens):
                trailing_percentage = _parse_percentage_token(tokens[next_index])
                if trailing_percentage is not None:
                    _add_composition_entry(composition, " ".join(words), str(trailing_percentage))
                    index = next_index + 1
                    continue
        index += 1
    return composition


def _add_composition_entry(composition: dict[str, float], material: str, percentage: str) -> None:
    candidate = material.strip()
    key = FABRIC_ALIASES.get(candidate)
    if key is None and " " in candidate:
        words = candidate.split()
        for length in range(len(words), 0, -1):
            key = FABRIC_ALIASES.get(" ".join(words[:length]))
            if key is not None:
                break
    if key is None:
        first_word = candidate.split()[0] if candidate.split() else candidate
        for stem, mapped in FABRIC_STEMS.items():
            if first_word.startswith(stem):
                key = mapped
                break
    if not key:
        return
    value = max(0, min(int(percentage), 100))
    composition[key] = max(composition.get(key, 0.0), float(value))


def _parse_origin(raw_text: str) -> str | None:
    lowered = raw_text.lower()
    for country in KNOWN_COUNTRIES:
        if country.lower() in lowered:
            return country
    match = ORIGIN_PATTERN.search(raw_text)
    if not match:
        return None
    return match.group(1).strip()


def _parse_care_instructions(text: str) -> list[str]:
    instructions: list[str] = []
    for pattern in CARE_PATTERNS:
        instructions.extend(match.strip() for match in pattern.findall(text))
    return instructions


def _parse_brand(raw_text: str) -> str | None:
    match = BRAND_PATTERN.search(raw_text)
    if not match:
        return None
    return match.group(1).upper()


def _normalize(text: str) -> str:
    return normalize_ascii(text)


def _parse_percentage_token(token: str) -> int | None:
    cleaned = token.strip().replace("%", "")
    if not cleaned.isdigit():
        return None
    return int(cleaned)
