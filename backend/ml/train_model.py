from __future__ import annotations

import pickle
from pathlib import Path
import csv

from backend.ml.model_utils import FEATURE_COLUMNS, quality_from_rule


BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "data" / "fabric_data.csv"
MODEL_PATH = BASE_DIR / "backend" / "ml" / "fabric_model.pkl"


class RuleBasedFabricModel:
    def predict(self, rows: list[list[int]]) -> list[str]:
        predictions: list[str] = []
        for row in rows:
            fabrics = dict(zip(FEATURE_COLUMNS, row, strict=False))
            predictions.append(quality_from_rule(fabrics))
        return predictions


def _load_rows(dataset_path: Path) -> tuple[list[list[int]], list[str]]:
    rows: list[list[int]] = []
    labels: list[str] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append([int(item[column]) for column in FEATURE_COLUMNS])
            labels.append(item["quality_label"])
    return rows, labels


def _fallback_report(rows: list[list[int]], labels: list[str]) -> str:
    model = RuleBasedFabricModel()
    predictions = model.predict(rows)
    correct = sum(1 for expected, predicted in zip(labels, predictions, strict=False) if expected == predicted)
    accuracy = correct / len(labels) if labels else 0
    return f"Fallback rule model accuracy: {accuracy:.2%}"


def train_model(dataset_path: Path = DATASET_PATH, model_path: Path = MODEL_PATH) -> str:
    rows, labels = _load_rows(dataset_path)
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split

        x_train, x_test, y_train, y_test = train_test_split(
            rows,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels,
        )

        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(x_train, y_train)
        report = classification_report(y_test, model.predict(x_test))
    except Exception:
        model = RuleBasedFabricModel()
        report = _fallback_report(rows, labels)

    with model_path.open("wb") as handle:
        pickle.dump(model, handle)
    return report


if __name__ == "__main__":
    print(train_model())
