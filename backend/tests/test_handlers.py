"""Tests for FastAPI handlers."""

import base64
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.models.schemas import ConverseResult
from src.utils.exceptions import BedrockError, RateLimitError


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    """Create a fresh FastAPI app for each test."""
    from src.app import create_app

    return create_app()


@pytest.fixture
async def client(app):  # type: ignore[no-untyped-def]
    """Async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.anyio
class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "model" in data
        assert "region" in data


@pytest.mark.anyio
class TestUsageEndpoint:
    @patch("src.handlers.health.get_rate_limiter")
    async def test_usage_returns_200(
        self, mock_get_limiter: MagicMock, client: AsyncClient
    ) -> None:
        mock_limiter = MagicMock()
        mock_limiter.get_current_usage.return_value = {
            "total_requests": 3,
            "limit": 10,
            "remaining": 7,
        }
        mock_get_limiter.return_value = mock_limiter

        response = await client.get("/api/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 3
        assert data["remaining"] == 7


@pytest.mark.anyio
class TestChatEndpoint:
    @patch("src.handlers.chat.get_bedrock_service")
    @patch("src.handlers.chat.get_rate_limiter")
    async def test_text_only_chat(
        self,
        mock_get_limiter: MagicMock,
        mock_get_bedrock: MagicMock,
        client: AsyncClient,
    ) -> None:
        mock_get_limiter.return_value = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = ConverseResult(
            text="Here is a description",
            usage={"inputTokens": 50},
            latency_ms=500,
        )
        mock_get_bedrock.return_value = mock_bedrock

        response = await client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": [{"text": "Describe a sunset"}]}
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Here is a description"
        assert data["image"] is None

    @patch("src.handlers.chat.get_bedrock_service")
    @patch("src.handlers.chat.get_rate_limiter")
    async def test_image_response(
        self,
        mock_get_limiter: MagicMock,
        mock_get_bedrock: MagicMock,
        client: AsyncClient,
    ) -> None:
        mock_get_limiter.return_value = MagicMock()
        fake_image = b"\x89PNGfakeimage"
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = ConverseResult(
            text="Generated image",
            image_bytes=fake_image,
            usage={"inputTokens": 100},
            latency_ms=1500,
        )
        mock_get_bedrock.return_value = mock_bedrock

        response = await client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": [{"text": "Generate a cat"}]}
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["image"] == base64.b64encode(fake_image).decode("utf-8")

    @patch("src.handlers.chat.get_rate_limiter")
    async def test_rate_limited_returns_429(
        self,
        mock_get_limiter: MagicMock,
        client: AsyncClient,
    ) -> None:
        mock_limiter = MagicMock()
        mock_limiter.check_rate_limit.side_effect = RateLimitError()
        mock_get_limiter.return_value = mock_limiter

        response = await client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": [{"text": "test"}]}
                ]
            },
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"

    @patch("src.handlers.chat.get_bedrock_service")
    @patch("src.handlers.chat.get_rate_limiter")
    async def test_bedrock_error_returns_502(
        self,
        mock_get_limiter: MagicMock,
        mock_get_bedrock: MagicMock,
        client: AsyncClient,
    ) -> None:
        mock_get_limiter.return_value = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.converse.side_effect = BedrockError("Model timed out")
        mock_get_bedrock.return_value = mock_bedrock

        response = await client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": [{"text": "test"}]}
                ]
            },
        )
        assert response.status_code == 502
        data = response.json()
        assert data["error_code"] == "BEDROCK_ERROR"

    async def test_invalid_request_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/chat", json={"not_messages": []})
        assert response.status_code == 422

    @patch("src.handlers.chat.get_bedrock_service")
    @patch("src.handlers.chat.get_rate_limiter")
    async def test_cors_headers_present(
        self,
        mock_get_limiter: MagicMock,
        mock_get_bedrock: MagicMock,
        client: AsyncClient,
    ) -> None:
        response = await client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        # CORS middleware should respond
        assert response.status_code in (200, 204)

    @patch("src.handlers.chat.get_bedrock_service")
    @patch("src.handlers.chat.get_rate_limiter")
    async def test_chat_with_image_input(
        self,
        mock_get_limiter: MagicMock,
        mock_get_bedrock: MagicMock,
        client: AsyncClient,
    ) -> None:
        mock_get_limiter.return_value = MagicMock()
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = ConverseResult(
            text="I see an image",
            usage={"inputTokens": 200},
            latency_ms=1000,
        )
        mock_get_bedrock.return_value = mock_bedrock

        img_b64 = base64.b64encode(b"fakeimage").decode("utf-8")
        response = await client.post(
            "/api/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": "Edit this image"},
                            {"image": {"format": "png", "data": img_b64}},
                        ],
                    }
                ]
            },
        )
        assert response.status_code == 200

        # Verify the converse call received decoded bytes
        call_args = mock_bedrock.converse.call_args
        messages = call_args.args[0] if call_args.args else call_args.kwargs["messages"]
        image_block = messages[0]["content"][1]
        assert image_block["image"]["source"]["bytes"] == b"fakeimage"
