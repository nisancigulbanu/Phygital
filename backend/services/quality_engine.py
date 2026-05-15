from __future__ import annotations

from backend.ml.textile_rules import FABRIC_QUALITY_SCORES, ORIGIN_BONUS


def calculate_price_performance(quality_score: float, price: float | None) -> float | None:
    """Compute quality points per 100 TL."""
    if price is None or price <= 0:
        return None
    return round((quality_score / price) * 100, 2)


def evaluate_quality(
    *,
    fabric_composition: dict[str, float],
    origin_country: str | None = None,
    price: float | None = None,
) -> dict[str, float | str | None]:
    """Produce a 0-100 score, grade, and optional price-performance score."""
    normalized = _normalize_quality_fabrics(fabric_composition)
    base_score = 0.0
    for fabric, ratio in normalized.items():
        weight = FABRIC_QUALITY_SCORES.get(fabric, 50)
        base_score += (ratio / 100.0) * weight

    quality_score = min(round(base_score + ORIGIN_BONUS.get(origin_country or "", 0), 2), 100.0)
    return {
        "quality_score": quality_score,
        "grade": _quality_grade(quality_score),
        "price_performance": calculate_price_performance(quality_score, price),
    }


def _quality_grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 75:
        return "B+"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def _normalize_quality_fabrics(fabrics: dict[str, float]) -> dict[str, float]:
    aliases = {
        "organic cotton": "pamuk",
        "recycled polyester": "polyester",
        "merino wool": "yun",
        "polyamide": "naylon",
        "polyamid": "naylon",
        "poliamit": "naylon",
        "viscose": "viskon",
        "viskoz": "viskon",
    }
    normalized: dict[str, float] = {}
    for key, value in fabrics.items():
        mapped = aliases.get(key, key)
        normalized[mapped] = normalized.get(mapped, 0.0) + float(value)
    return normalized
