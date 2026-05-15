from __future__ import annotations

from typing import Any

from backend.config import Settings

try:  # pragma: no cover - optional dependency
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


SYSTEM_PROMPT = (
    "Sen bir tekstil ve moda uzmansin. Kullanicilarin giysi etiketlerini tarayarak "
    "urun kalitesini anlamalarina yardimci oluyorsun. Kisa, acik ve samimi Turkce "
    "yanit ver. Teknik jargondan kacın."
)


class LLMService:
    """Advice and follow-up generation with an API-backed or rule-based fallback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = (
            anthropic.Anthropic(api_key=settings.anthropic_api_key)
            if anthropic is not None and settings.anthropic_api_key
            else None
        )

    def get_shopping_advice(self, scan_data: dict[str, Any]) -> str:
        """Generate shopping advice for a scan result."""
        if self._client is None:
            return self._fallback_advice(scan_data)

        user_message = (
            f"Kumas: {scan_data['fabric_composition']}\n"
            f"Mense: {scan_data.get('origin_country')}\n"
            f"Kalite skoru: {scan_data.get('quality_score')}/100\n"
            f"Fiyat: {scan_data.get('price', 'bilinmiyor')} TL\n"
            f"Fiyat/performans: {scan_data.get('price_performance', 'N/A')}\n"
            f"Alternatifler: {scan_data.get('alternatives', [])}\n"
            "Bu veriler isiginda kisa bir alisveris tavsiyesi ver."
        )
        response = self._client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()

    def chat_about_scan(self, *, message: str, scan_data: dict[str, Any]) -> str:
        """Reply to a follow-up question about a scan."""
        if self._client is None:
            return (
                f"Soru: {message} "
                f"Bu urun icin kalite skoru {scan_data.get('quality_score', 'bilinmiyor')} ve "
                f"baskin kumaslar {scan_data.get('fabric_composition', {})}. "
                "Dogal lif orani dusukse daha iyi alternatiflere yonelmek mantikli olur."
            )

        user_message = (
            f"Kontekst: {scan_data}\n"
            f"Kullanici sorusu: {message}\n"
            "Yaniti 3 cumleyi gecmeden ver."
        )
        response = self._client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=250,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()

    def _fallback_advice(self, scan_data: dict[str, Any]) -> str:
        fabrics = scan_data.get("fabric_composition", {})
        quality_score = scan_data.get("quality_score")
        price = scan_data.get("price")
        alternatives = scan_data.get("alternatives", [])
        dominant = ", ".join(f"{int(v)}% {k}" for k, v in fabrics.items()) or "belirsiz kumas"
        if quality_score is None:
            return "Etiketten yeterli kumas bilgisi cikmadi. Daha net bir foto ile tekrar tarama yapmak en dogru adim."
        alt_note = " Daha yuksek skorlu alternatifler listelendi." if alternatives else ""
        return (
            f"Urunun baskin icerigi {dominant}. Kalite skoru {quality_score}/100 oldugu icin "
            f"{'guclu bir secim sayilabilir' if quality_score >= 75 else 'almadan once dikkatli karsilastirilmasi gerekir'}. "
            f"Fiyat bilgisi {price if price is not None else 'yok'} TL.{alt_note}"
        )
