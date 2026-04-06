"""Chat endpoint handler for Bedrock Converse API."""

from __future__ import annotations

import base64
import binascii
from typing import Any

from fastapi import APIRouter, HTTPException

from src.models.schemas import (
    VALID_IMAGE_FORMATS,
    ChatRequest,
    ChatResponse,
    ImageBlock,
    TextBlock,
)
from src.services.bedrock_service import get_bedrock_service
from src.services.rate_limiter import get_rate_limiter

router = APIRouter(prefix="/api")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat request through the Bedrock Converse API."""
    # Check rate limit
    get_rate_limiter().check_rate_limit()

    # Convert frontend message format to Converse API format
    messages = _convert_messages(request.messages)

    # Build inference config
    inference_config: dict[str, Any] | None = None
    if request.inferenceConfig:
        config_dict: dict[str, Any] = {}
        if request.inferenceConfig.maxTokens is not None:
            config_dict["maxTokens"] = request.inferenceConfig.maxTokens
        if request.inferenceConfig.temperature is not None:
            config_dict["temperature"] = request.inferenceConfig.temperature
        if request.inferenceConfig.topP is not None:
            config_dict["topP"] = request.inferenceConfig.topP
        if request.inferenceConfig.topK is not None:
            config_dict["topK"] = request.inferenceConfig.topK
        if config_dict:
            inference_config = config_dict

    # Call Bedrock
    result = get_bedrock_service().converse(messages, inference_config)

    # Convert result to response
    image_b64: str | None = None
    image_format: str | None = None
    if result.image_bytes:
        image_b64 = base64.b64encode(result.image_bytes).decode("utf-8")
        image_format = result.image_format

    return ChatResponse(
        text=result.text,
        image=image_b64,
        image_format=image_format,
        usage=result.usage,
        latency_ms=result.latency_ms,
    )


def _convert_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """Convert frontend message format to Converse API format."""
    converted: list[dict[str, Any]] = []

    for msg in messages:
        content_blocks: list[dict[str, Any]] = []

        for block in msg.content:
            if isinstance(block, TextBlock):
                content_blocks.append({"text": block.text})
            elif isinstance(block, ImageBlock):
                fmt = block.image.format
                if fmt not in VALID_IMAGE_FORMATS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported image format: {fmt}",
                    )
                try:
                    image_bytes = base64.b64decode(block.image.data)
                except binascii.Error as e:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid base64 image data",
                    ) from e
                content_blocks.append(
                    {
                        "image": {
                            "format": fmt,
                            "source": {"bytes": image_bytes},
                        }
                    }
                )

        converted.append({"role": msg.role, "content": content_blocks})

    return converted
