from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


FABRIC_KEYS = (
    "pamuk",
    "polyester",
    "akrilik",
    "elastan",
    "yun",
    "viskon",
    "keten",
    "ipek",
    "naylon",
)

QualityLabel = Literal["A", "B+", "B", "C", "D"]
LegacyQualityLabel = Literal["iyi", "orta", "kotu"]


class ScanRequest(BaseModel):
    """Request payload for image-based label scanning."""

    image: str = Field(min_length=1, description="Base64 encoded JPEG/PNG or demo text bytes.")
    price: float | None = Field(default=None, ge=0)


class OCRResult(BaseModel):
    """Normalized OCR output."""

    raw_text: str
    confidence: float
    provider: str


class ScanResult(BaseModel):
    """Primary response contract for the scan flow."""

    raw_text: str
    fabric_composition: dict[str, float] = Field(default_factory=dict)
    origin_country: str | None = None
    care_instructions: list[str] = Field(default_factory=list)
    brand: str | None = None
    quality_score: float | None = None
    quality_grade: QualityLabel | None = None
    price_performance: float | None = None
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    llm_advice: str
    scan_id: str


class ChatRequest(BaseModel):
    """Follow-up conversation request for a previous scan."""

    message: str = Field(min_length=1, max_length=2000)
    context: ScanResult


class ChatResponse(BaseModel):
    """Chat reply response."""

    reply: str


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
    version: str


class AlternativesResponse(BaseModel):
    """Alternative product suggestions."""

    alternatives: list[dict[str, Any]]


class AnalyzeRequest(BaseModel):
    """Legacy analyze request kept for compatibility."""

    user_id: str = Field(min_length=1, max_length=128)
    brand: str = Field(default="", max_length=120)
    price: float = Field(default=0.0, ge=0)
    fabrics: dict[str, int | float] = Field(default_factory=dict)
    product_name: str = Field(default="", max_length=240)
    source_url: str = Field(default="", max_length=2048)

    @field_validator("brand")
    @classmethod
    def normalize_brand(cls, value: str) -> str:
        return value.strip().lower()


class AnalyzeResponse(BaseModel):
    """Legacy analyze response kept for compatibility."""

    analysis_id: str
    fabric: dict[str, int | float]
    quality: LegacyQualityLabel
    eco_score: int | None = None
    recommendation: str
    product_name: str = ""


class ProductLookupRequest(BaseModel):
    """Request payload for product URL extraction."""

    product_url: str = Field(default="", max_length=2048)
    page_text: str = Field(default="", max_length=30000)

    @model_validator(mode="after")
    def validate_source(self):
        if not self.product_url.strip() and not self.page_text.strip():
            raise ValueError("product_url veya page_text gerekli")
        return self


class ProductLookupResponse(BaseModel):
    """Product extraction result."""

    title: str = ""
    brand: str = ""
    price: float | None = None
    image_url: str = ""
    fabrics: dict[str, int] = Field(default_factory=dict)
    extracted_text: str = ""
    notes: str = ""
