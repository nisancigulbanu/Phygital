from backend.config import Settings
from backend.services.llm_service import LLMService
from backend.services.recommender import RecommendationService


def test_llm_service_falls_back_when_client_raises():
    settings = Settings()
    service = LLMService(settings)

    class StubMessages:
        def create(self, **kwargs):
            raise RuntimeError("upstream_failed")

    class StubClient:
        messages = StubMessages()

    service._client = StubClient()
    result = service.get_shopping_advice(
        {
            "fabric_composition": {"pamuk": 80, "polyester": 20},
            "quality_score": 72,
            "price": 499,
            "alternatives": [],
        }
    )
    assert "Kalite skoru" in result or "kalite skoru" in result


def test_recommendation_service_falls_back_when_client_raises():
    settings = Settings()
    service = RecommendationService(settings)

    class StubResponses:
        def create(self, **kwargs):
            raise RuntimeError("upstream_failed")

    class StubClient:
        responses = StubResponses()

    service._client = StubClient()
    result = service.generate(
        fabrics={"pamuk": 70, "polyester": 30},
        quality="iyi",
        brand="demo",
        eco_score=7,
        price=799,
    )
    assert "kalite skoru" in result.lower()
