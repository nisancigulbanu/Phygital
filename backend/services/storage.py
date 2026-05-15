from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import logging
from uuid import uuid4

from backend.config import Settings

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover
    Client = None
    create_client = None


logger = logging.getLogger(__name__)


@dataclass
class AnalysisRecord:
    analysis_id: str
    eco_score: int | None


class StorageService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Client | None = None
        if settings.supabase_url and settings.supabase_key and create_client is not None:
            self._client = create_client(settings.supabase_url, settings.supabase_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def get_brand_score(self, brand: str) -> int | None:
        if not brand or self._client is None:
            return None

        try:
            response = (
                self._client.table(self.settings.supabase_brands_table)
                .select("eco_score")
                .eq("name", brand)
                .limit(1)
                .execute()
            )
        except Exception:
            logger.exception("Brand eco score okunamadi: brand=%s", brand)
            return None
        if response.data:
            return response.data[0].get("eco_score")
        return None

    def save_analysis(
        self,
        *,
        user_id: str,
        brand: str,
        price: float,
        fabrics: dict[str, int],
        quality: str,
        recommendation: str,
        product_name: str = "",
        source_url: str = "",
    ) -> AnalysisRecord:
        analysis_id = str(uuid4())
        eco_score = self.get_brand_score(brand)
        if self._client is None:
            return AnalysisRecord(analysis_id=analysis_id, eco_score=eco_score)

        payload = {
            "id": analysis_id,
            "user_id": user_id,
            "fabric_data": fabrics,
            "quality": quality,
            "brand": brand,
            "price": price,
            "recommendation": recommendation,
            "product_name": product_name,
            "source_url": source_url,
            "created_at": datetime.now(UTC).isoformat(),
        }
        try:
            self._client.table(self.settings.supabase_analyses_table).insert(payload).execute()
        except Exception:
            logger.exception("Analiz Supabase'e kaydedilemedi: analysis_id=%s", analysis_id)
        return AnalysisRecord(analysis_id=analysis_id, eco_score=eco_score)
