from __future__ import annotations


DEMO_ALTERNATIVES = [
    {
        "product_id": "demo_001",
        "name": "Organik Pamuklu Basic T-Shirt",
        "brand": "Beden",
        "fabric": {"organik pamuk": 95, "elastan": 5},
        "quality_score": 87,
        "price": 249,
        "image_url": "https://example.com/demo-001.jpg",
        "buy_url": "https://example.com/demo-001",
    },
    {
        "product_id": "demo_002",
        "name": "Keten Karisim Overshirt",
        "brand": "Atelier",
        "fabric": {"keten": 55, "pamuk": 45},
        "quality_score": 81,
        "price": 399,
        "image_url": "https://example.com/demo-002.jpg",
        "buy_url": "https://example.com/demo-002",
    },
    {
        "product_id": "demo_003",
        "name": "Merino Knit Polo",
        "brand": "North Loom",
        "fabric": {"merinos": 100},
        "quality_score": 92,
        "price": 899,
        "image_url": "https://example.com/demo-003.jpg",
        "buy_url": "https://example.com/demo-003",
    },
]


class SimilarityEngine:
    """Demo alternative finder with a deterministic in-memory catalog."""

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode

    def find_alternatives(self, *, current_quality_score: float) -> list[dict]:
        if not self.demo_mode:
            return []
        return [
            item
            for item in DEMO_ALTERNATIVES
            if item["quality_score"] > current_quality_score
        ][:3]
