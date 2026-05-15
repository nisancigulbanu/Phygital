from __future__ import annotations

import re

from backend.utils.text_normalization import normalize_ascii


FABRIC_KEYWORDS = {
    "pamuk": "cotton",
    "cotton": "cotton",
    "polyester": "polyester",
    "polyesteri": "polyester",
    "polyamid": "polyamide",
    "polyami": "polyamide",
    "poliamit": "polyamide",
    "poliami": "polyamide",
    "polyamide": "polyamide",
    "naylon": "polyamide",
    "nylon": "polyamide",
    "akrilik": "acrylic",
    "acrylic": "acrylic",
    "elastan": "elastane",
    "elastane": "elastane",
    "spandex": "elastane",
    "yun": "wool",
    "wool": "wool",
    "viskon": "viscose",
    "viskoz": "viscose",
    "viscose": "viscose",
    "organic cotton": "organic cotton",
    "organik pamuk": "organic cotton",
    "recycled polyester": "recycled polyester",
    "geri donusturulmus polyester": "recycled polyester",
    "merino wool": "merino wool",
    "merinos yun": "merino wool",
    "keten": "linen",
    "linen": "linen",
}

FABRIC_STEMS = {
    "pamuk": "cotton",
    "cotton": "cotton",
    "polyester": "polyester",
    "polyamid": "polyamide",
    "polyami": "polyamide",
    "poliamit": "polyamide",
    "poliami": "polyamide",
    "polyamide": "polyamide",
    "naylon": "polyamide",
    "nylon": "polyamide",
    "akrilik": "acrylic",
    "acrylic": "acrylic",
    "elastan": "elastane",
    "elastane": "elastane",
    "spandex": "elastane",
    "yun": "wool",
    "wool": "wool",
    "viskon": "viscose",
    "viskoz": "viscose",
    "viscose": "viscose",
    "keten": "linen",
    "linen": "linen",
}

LETTER_PATTERN = r"[^\W\d_]"
MATERIAL_PATTERN = "(" + LETTER_PATTERN + "+(?:[\\s/-]+" + LETTER_PATTERN + "+){0,2})"


def _normalize(text: str) -> str:
    return normalize_ascii(text)


def extract_fabrics_from_text(text: str) -> dict[str, int]:
    normalized = _normalize(text)
    results: dict[str, int] = {}
    patterns = (
        re.compile(rf"%\s*(\d{{1,3}})\s*{MATERIAL_PATTERN}", re.IGNORECASE),
        re.compile(rf"(\d{{1,3}})\s*%\s*{MATERIAL_PATTERN}", re.IGNORECASE),
    )
    for pattern in patterns:
        for percentage, keyword in pattern.findall(normalized):
            mapped = _normalize_fabric_keyword(keyword)
            if mapped:
                results[mapped] = int(percentage)

    for line in re.split(r"[\n,;]+", normalized):
        line = line.strip()
        match = re.match(rf"^{MATERIAL_PATTERN}\s+(\d{{1,3}})$", line)
        if not match:
            continue
        keyword, percentage = match.groups()
        mapped = _normalize_fabric_keyword(keyword)
        if mapped:
            results[mapped] = int(percentage)
    return results


def _normalize_fabric_keyword(keyword: str) -> str:
    cleaned = keyword.strip()
    if cleaned in FABRIC_KEYWORDS:
        return FABRIC_KEYWORDS[cleaned]
    words = cleaned.split()
    for length in range(len(words), 0, -1):
        candidate = " ".join(words[:length])
        if candidate in FABRIC_KEYWORDS:
            return FABRIC_KEYWORDS[candidate]
    first_word = words[0] if words else cleaned
    for stem, mapped in FABRIC_STEMS.items():
        if first_word.startswith(stem):
            return mapped
    return ""
