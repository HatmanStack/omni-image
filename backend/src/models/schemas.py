"""Pydantic models and dataclasses for API request/response shapes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConverseResult:
    """Result from a Bedrock Converse API call."""

    text: str | None = None
    image_bytes: bytes | None = None
    image_format: str = "png"
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0
