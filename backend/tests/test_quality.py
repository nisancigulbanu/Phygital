from backend.services.quality_engine import calculate_price_performance, evaluate_quality


def test_quality_scoring():
    result = evaluate_quality(
        fabric_composition={"pamuk": 80, "polyester": 20},
        origin_country="Turkey",
        price=400,
    )
    assert result["quality_score"] == 68.6
    assert result["grade"] == "B"


def test_price_performance():
    assert calculate_price_performance(80, 400) == 20.0
