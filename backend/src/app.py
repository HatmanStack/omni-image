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
from src.utils.logger import app_logger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="Omni Image API", version="1.0.0")

    # CORS middleware
    config = get_config()
    origins = [o.strip() for o in config.allowed_origins.split(",") if o.strip()]
    has_specific_origins = origins != ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=has_specific_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
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
        app_logger.error(f"Bedrock error on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                error="Image generation failed. Please try again.",
                error_code=exc.error_code or "BEDROCK_ERROR",
            ).model_dump(),
        )

    @application.exception_handler(OmniImageError)
    async def omni_image_error_handler(request: Request, exc: OmniImageError) -> JSONResponse:
        app_logger.error(f"Application error on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="An unexpected error occurred. Please try again.",
                error_code=exc.error_code or "INTERNAL_ERROR",
            ).model_dump(),
        )

    @application.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        app_logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc!s}")
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
