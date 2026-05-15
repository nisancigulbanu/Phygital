from __future__ import annotations

import logging
from backend.config import Settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key and OpenAI else None

    def build_fallback(
        self,
        *,
        fabrics: dict[str, int],
        quality: str,
        brand: str,
        eco_score: int | None,
        price: float,
    ) -> str:
        dominant = ", ".join(f"{value}% {key}" for key, value in fabrics.items() if value > 0) or "belirsiz kumas"
        score_text = f"{eco_score}/10" if eco_score is not None else "bilinmiyor"
        return (
            f"Bu urunde baskin icerik {dominant} ve kalite skoru {quality}. "
            f"{brand or 'Marka'} icin etik skor {score_text}; {price:.0f} TL seviyesinde satin almadan once "
            "daha yuksek dogal lif oranli bir alternatif olup olmadigina da bakman faydali olur."
        )

    def generate(
        self,
        *,
        fabrics: dict[str, int],
        quality: str,
        brand: str,
        eco_score: int | None,
        price: float,
    ) -> str:
        if self._client is None:
            return self.build_fallback(
                fabrics=fabrics,
                quality=quality,
                brand=brand,
                eco_score=eco_score,
                price=price,
            )

        prompt = (
            "Sen surdurulebilir moda danismani olarak kisa ve pratik bir yorum yapiyorsun. "
            "Cevabin Turkce, 2-3 cumle ve satin alma karari icin net olsun.\n"
            f"Kumas dagilimi: {fabrics}\n"
            f"Kalite skoru: {quality}\n"
            f"Marka: {brand or 'bilinmiyor'}\n"
            f"Etik skor: {eco_score if eco_score is not None else 'bilinmiyor'}\n"
            f"Fiyat: {price:.2f} TL"
        )

        try:
            response = self._client.responses.create(
                model=self.settings.openai_model,
                input=prompt,
            )
            return response.output_text.strip()
        except Exception:
            logger.exception("OpenAI recommendation uretilemedi, fallback kullaniliyor.")
            return self.build_fallback(
                fabrics=fabrics,
                quality=quality,
                brand=brand,
                eco_score=eco_score,
                price=price,
            )

    def legacy_quality_from_fabrics(self, fabrics: dict[str, int | float]) -> dict[str, str]:
        """Map simple fabric ratios to the old qualitative labels."""
        normalized = self._normalize_legacy_fabrics(fabrics)
        natural = float(normalized.get("pamuk", 0)) + float(normalized.get("yun", 0)) + float(normalized.get("viskon", 0)) + float(normalized.get("keten", 0))
        acrylic = float(normalized.get("akrilik", 0))
        if acrylic > 30 or natural < 40:
            return {"grade": "kotu"}
        if natural >= 60:
            return {"grade": "iyi"}
        return {"grade": "orta"}

    def _normalize_legacy_fabrics(self, fabrics: dict[str, int | float]) -> dict[str, float]:
        aliases = {
            "cotton": "pamuk",
            "pamuk": "pamuk",
            "wool": "yun",
            "yun": "yun",
            "viscose": "viskon",
            "viskon": "viskon",
            "viskoz": "viskon",
            "linen": "keten",
            "keten": "keten",
            "acrylic": "akrilik",
            "akrilik": "akrilik",
            "polyamide": "naylon",
            "polyamid": "naylon",
            "poliamit": "naylon",
            "naylon": "naylon",
            "nylon": "naylon",
            "organic cotton": "pamuk",
            "recycled polyester": "polyester",
            "merino wool": "yun",
            "polyester": "polyester",
            "elastane": "elastan",
            "elastan": "elastan",
        }
        normalized: dict[str, float] = {}
        for key, value in fabrics.items():
            mapped = aliases.get(str(key).strip().lower(), str(key).strip().lower())
            normalized[mapped] = normalized.get(mapped, 0.0) + float(value or 0)
        return normalized
