"""Pydantic models and dataclasses for API request/response shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Dataclasses (internal) ---


@dataclass
class ConverseResult:
    """Result from a Bedrock Converse API call."""

    text: str | None = None
    image_bytes: bytes | None = None
    image_format: str = "png"
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0


# --- Request models (Pydantic) ---


class TextBlock(BaseModel):
    """Text content block."""

    text: str


VALID_IMAGE_FORMATS = frozenset({"png", "jpeg", "gif", "webp"})


class ImageSource(BaseModel):
    """Image source with format and base64 data."""

    format: str
    data: str


class ImageBlock(BaseModel):
    """Image content block."""

    image: ImageSource


class Message(BaseModel):
    """A single message in the conversation."""

    role: Literal["user", "assistant"]
    content: list[TextBlock | ImageBlock] = Field(min_length=1)


class InferenceConfig(BaseModel):
    """Optional inference configuration for the Converse API."""

    maxTokens: int | None = None
    temperature: float | None = None
    topP: float | None = None
    topK: int | None = None


class ChatRequest(BaseModel):
    """Request payload for the chat endpoint."""

    messages: list[Message] = Field(min_length=1)
    inferenceConfig: InferenceConfig | None = None


# --- Response models (Pydantic) ---


class ChatResponse(BaseModel):
    """Response payload from the chat endpoint."""

    text: str | None = None
    image: str | None = None  # base64-encoded PNG
    usage: dict[str, Any] | None = None
    latency_ms: int | None = None


class ErrorResponse(BaseModel):
    """Error response payload."""

    error: str
    error_code: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model: str
    region: str


class UsageResponse(BaseModel):
    """Rate limit usage response."""

    total_requests: int
    limit: int
    remaining: int
