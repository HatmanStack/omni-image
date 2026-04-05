"""Health check and usage endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.models.config import get_config
from src.models.schemas import HealthResponse, UsageResponse
from src.services.rate_limiter import get_rate_limiter

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    config = get_config()
    return HealthResponse(
        status="ok",
        model=config.nova_omni_model,
        region=config.bedrock_region,
    )


@router.get("/usage", response_model=UsageResponse)
async def usage() -> UsageResponse:
    """Get current rate limit usage."""
    data = get_rate_limiter().get_current_usage()
    return UsageResponse(**data)
