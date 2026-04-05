"""Chat endpoint handler for Bedrock Converse API."""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter

from src.models.schemas import (
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
    if result.image_bytes:
        image_b64 = base64.b64encode(result.image_bytes).decode("utf-8")

    return ChatResponse(
        text=result.text,
        image=image_b64,
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
                img = block.image
                fmt = img.get("format", "png")
                data_b64 = img.get("data", "")
                image_bytes = base64.b64decode(data_b64)
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
