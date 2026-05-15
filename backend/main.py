from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ProductLookupRequest,
    ProductLookupResponse,
    ScanRequest,
    ScanResult,
)
from backend.routers.alternatives import router as alternatives_router
from backend.routers.chat import router as chat_router
from backend.routers.scan import router as scan_router
from backend.services.llm_service import LLMService
from backend.services.product_lookup import ProductLookupService
from backend.services.recommender import RecommendationService
from backend.services.similarity_engine import SimilarityEngine
from backend.services.storage import StorageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.storage = StorageService(settings)
    app.state.recommender = RecommendationService(settings)
    app.state.product_lookup = ProductLookupService()
    app.state.similarity_engine = SimilarityEngine(demo_mode=settings.demo_mode)
    app.state.llm_service = LLMService(settings)
    yield


app = FastAPI(title="FabricScan API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(scan_router)
app.include_router(chat_router)
app.include_router(alternatives_router)


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    def _run() -> AnalyzeResponse:
        quality_result = app.state.recommender.legacy_quality_from_fabrics(payload.fabrics)
        eco_score = app.state.storage.get_brand_score(payload.brand)
        recommendation = app.state.recommender.generate(
            fabrics=payload.fabrics,
            quality=quality_result["grade"],
            brand=payload.brand,
            eco_score=eco_score,
            price=payload.price,
        )
        record = app.state.storage.save_analysis(
            user_id=payload.user_id,
            brand=payload.brand,
            price=payload.price,
            fabrics=payload.fabrics,
            quality=quality_result["grade"],
            recommendation=recommendation,
            product_name=payload.product_name,
            source_url=payload.source_url,
        )
        return AnalyzeResponse(
            analysis_id=record.analysis_id,
            fabric={key: value for key, value in payload.fabrics.items() if value > 0},
            quality=quality_result["grade"],
            eco_score=record.eco_score,
            recommendation=recommendation,
            product_name=payload.product_name,
        )

    return await run_in_threadpool(_run)


@app.post("/extract-product", response_model=ProductLookupResponse)
async def extract_product(payload: ProductLookupRequest) -> ProductLookupResponse:
    return await run_in_threadpool(
        app.state.product_lookup.fetch_product,
        product_url=payload.product_url,
        page_text=payload.page_text,
    )
