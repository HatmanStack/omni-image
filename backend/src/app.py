"""FastAPI application creation and configuration."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.handlers.chat import router as chat_router
from src.handlers.health import router as health_router
from src.models.config import get_config
from src.models.schemas import ErrorResponse
from src.utils.exceptions import BedrockError, OmniImageError, RateLimitError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="Omni Image API", version="1.0.0")

    # CORS middleware
    config = get_config()
    origins = [o.strip() for o in config.allowed_origins.split(",")]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @application.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error=exc.message,
                error_code=exc.error_code or "RATE_LIMIT_EXCEEDED",
            ).model_dump(),
        )

    @application.exception_handler(BedrockError)
    async def bedrock_error_handler(request: Request, exc: BedrockError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error=exc.message,
                error_code=exc.error_code or "BEDROCK_ERROR",
            ).model_dump(),
        )

    @application.exception_handler(OmniImageError)
    async def omni_image_error_handler(
        request: Request, exc: OmniImageError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=exc.message,
                error_code=exc.error_code or "INTERNAL_ERROR",
            ).model_dump(),
        )

    @application.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                error_code="INTERNAL_ERROR",
            ).model_dump(),
        )

    # Include routers
    application.include_router(chat_router)
    application.include_router(health_router)

    return application


app = create_app()
