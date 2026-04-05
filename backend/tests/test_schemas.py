"""Tests for Pydantic request/response schemas."""

import pytest
from pydantic import ValidationError

from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    ImageBlock,
    InferenceConfig,
    Message,
    TextBlock,
    UsageResponse,
)


class TestChatRequest:
    def test_valid_text_request(self) -> None:
        req = ChatRequest(
            messages=[
                Message(
                    role="user",
                    content=[TextBlock(text="Generate an image of a cat")],
                )
            ]
        )
        assert len(req.messages) == 1
        assert req.messages[0].role == "user"

    def test_missing_messages_raises(self) -> None:
        with pytest.raises(ValidationError):
            ChatRequest()  # type: ignore[call-arg]

    def test_text_and_image_content(self) -> None:
        msg = Message(
            role="user",
            content=[
                TextBlock(text="Edit this image"),
                ImageBlock(image={"format": "png", "data": "base64data"}),
            ],
        )
        assert len(msg.content) == 2

    def test_inference_config_all_optional(self) -> None:
        config = InferenceConfig()
        assert config.maxTokens is None
        assert config.temperature is None
        assert config.topP is None
        assert config.topK is None

    def test_inference_config_with_values(self) -> None:
        config = InferenceConfig(maxTokens=1000, temperature=0.7)
        assert config.maxTokens == 1000
        assert config.temperature == 0.7

    def test_request_with_inference_config(self) -> None:
        req = ChatRequest(
            messages=[
                Message(role="user", content=[TextBlock(text="test")])
            ],
            inferenceConfig=InferenceConfig(maxTokens=500),
        )
        assert req.inferenceConfig is not None
        assert req.inferenceConfig.maxTokens == 500


class TestChatResponse:
    def test_text_only_response(self) -> None:
        resp = ChatResponse(text="Here is your image description")
        assert resp.text == "Here is your image description"
        assert resp.image is None

    def test_text_and_image_response(self) -> None:
        resp = ChatResponse(
            text="Generated image",
            image="base64imagedata",
            usage={"inputTokens": 100},
            latency_ms=1500,
        )
        assert resp.image == "base64imagedata"
        assert resp.latency_ms == 1500

    def test_serialization(self) -> None:
        resp = ChatResponse(text="test", usage={"inputTokens": 50})
        data = resp.model_dump()
        assert data["text"] == "test"
        assert data["image"] is None


class TestErrorResponse:
    def test_serialization(self) -> None:
        resp = ErrorResponse(error="Rate limit exceeded", error_code="RATE_LIMIT_EXCEEDED")
        data = resp.model_dump()
        assert data["error"] == "Rate limit exceeded"
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"


class TestHealthResponse:
    def test_serialization(self) -> None:
        resp = HealthResponse(status="ok", model="nova-2-omni", region="us-west-2")
        data = resp.model_dump()
        assert data["status"] == "ok"


class TestUsageResponse:
    def test_serialization(self) -> None:
        resp = UsageResponse(total_requests=5, limit=10, remaining=5)
        assert resp.remaining == 5
