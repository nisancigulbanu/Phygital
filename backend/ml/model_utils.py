from __future__ import annotations

import pickle
from pathlib import Path

from backend.schemas import FABRIC_KEYS, QualityLabel


FEATURE_COLUMNS = list(FABRIC_KEYS)


def normalize_fabrics(fabrics: dict[str, int | float] | None) -> dict[str, int]:
    source = fabrics or {}
    normalized = {key: int(round(float(source.get(key, 0) or 0))) for key in FEATURE_COLUMNS}
    return normalized


def quality_from_rule(fabrics: dict[str, int]) -> QualityLabel:
    natural_score = fabrics["cotton"] + fabrics["wool"] + fabrics["viscose"] + fabrics["linen"]
    if fabrics["acrylic"] > 30 or natural_score < 40:
        return "kotu"
    if natural_score >= 60:
        return "iyi"
    return "orta"


def load_model(model_path: Path):
    if not model_path.exists():
        return None
    with model_path.open("rb") as handle:
        return pickle.load(handle)


def predict_quality(model, fabrics: dict[str, int]) -> QualityLabel:
    if model is None:
        return quality_from_rule(fabrics)
    feature_vector = [fabrics[column] for column in FEATURE_COLUMNS]
    prediction = model.predict([feature_vector])[0]
    return str(prediction)
