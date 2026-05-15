from __future__ import annotations

import base64
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from backend.models.schemas import ScanRequest, ScanResult
from backend.services.nlp_parser import parse_label_text
from backend.services.ocr_service import OCRServiceError, extract_text
from backend.services.quality_engine import evaluate_quality


router = APIRouter(prefix="/api/v1", tags=["scan"])


@router.post("/scan", response_model=ScanResult)
async def scan_label(payload: ScanRequest, request: Request) -> ScanResult:
    """Scan a fabric label image and return the normalized product analysis."""
    try:
        image_bytes = base64.b64decode(payload.image, validate=True)
    except Exception as exc:  # pragma: no cover - exercised by FastAPI validation path
        raise HTTPException(status_code=400, detail="invalid_image_base64") from exc

    def _run_scan() -> ScanResult:
        try:
            ocr_result = extract_text(image_bytes, settings=request.app.state.settings)
        except OCRServiceError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        parsed = parse_label_text(ocr_result["raw_text"])
        if parsed.get("error") == "fabric_not_found":
            return ScanResult(
                raw_text=ocr_result["raw_text"],
                fabric_composition={},
                origin_country=parsed.get("origin_country"),
                care_instructions=parsed.get("care_instructions", []),
                brand=parsed.get("brand"),
                quality_score=None,
                quality_grade=None,
                price_performance=None,
                alternatives=[],
                llm_advice="Etikette kumas bilgisi net secilemedi. Farkli aci veya daha net bir foto ile tekrar deneyin.",
                scan_id=str(uuid4()),
            )

        quality = evaluate_quality(
            fabric_composition=parsed["fabric_composition"],
            origin_country=parsed.get("origin_country"),
            price=payload.price,
        )
        alternatives = request.app.state.similarity_engine.find_alternatives(
            current_quality_score=quality["quality_score"],
        )
        advice = request.app.state.llm_service.get_shopping_advice(
            {
                "fabric_composition": parsed["fabric_composition"],
                "origin_country": parsed.get("origin_country"),
                "care_instructions": parsed.get("care_instructions", []),
                "brand": parsed.get("brand"),
                "quality_score": quality["quality_score"],
                "quality_grade": quality["grade"],
                "price": payload.price,
                "price_performance": quality["price_performance"],
                "alternatives": alternatives,
            }
        )
        return ScanResult(
            raw_text=ocr_result["raw_text"],
            fabric_composition=parsed["fabric_composition"],
            origin_country=parsed.get("origin_country"),
            care_instructions=parsed.get("care_instructions", []),
            brand=parsed.get("brand"),
            quality_score=quality["quality_score"],
            quality_grade=quality["grade"],
            price_performance=quality["price_performance"],
            alternatives=alternatives,
            llm_advice=advice,
            scan_id=str(uuid4()),
        )

    return await run_in_threadpool(_run_scan)
