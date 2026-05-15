from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from backend.models.schemas import ChatRequest, ChatResponse


router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Generate a follow-up answer for a scan result."""
    reply = await run_in_threadpool(
        request.app.state.llm_service.chat_about_scan,
        message=payload.message,
        scan_data=payload.context.model_dump(),
    )
    return ChatResponse(reply=reply)
