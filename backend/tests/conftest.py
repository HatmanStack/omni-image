"""Shared test fixtures for Omni Image backend."""

import json
import os
from unittest.mock import MagicMock

import pytest

# Set environment variables before any imports that use config
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-access-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-secret-key")
os.environ.setdefault("AWS_REGION", "us-west-2")
os.environ.setdefault("NOVA_IMAGE_BUCKET", "test-bucket")
os.environ.setdefault("BEDROCK_REGION", "us-west-2")


@pytest.fixture(autouse=True)
def _reset_config_between_tests() -> None:  # type: ignore[misc]
    """Reset config singleton between tests for isolation."""
    from src.models.config import reset_config

    reset_config()
    yield  # type: ignore[misc]
    reset_config()


@pytest.fixture
def mock_config():  # type: ignore[no-untyped-def]
    """Mock application configuration for tests that need custom config values."""
    from unittest.mock import patch

    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "test-access-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key",
            "AWS_REGION": "us-west-2",
            "NOVA_IMAGE_BUCKET": "test-bucket",
            "BEDROCK_REGION": "us-west-2",
            "RATE_LIMIT": "10",
            "RATE_LIMIT_WINDOW": "3600",
            "LOG_LEVEL": "INFO",
            "ALLOWED_ORIGINS": "*",
        },
    ):
        from src.models.config import get_config, reset_config

        reset_config()
        config = get_config()
        yield config
        reset_config()


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Mock S3 client with common operations."""
    mock = MagicMock()
    mock.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps({"timestamps": []}).encode()),
        "ETag": '"abc123"',
    }
    mock.put_object.return_value = {}
    return mock


@pytest.fixture
def mock_converse_response() -> dict:  # type: ignore[type-arg]
    """Realistic Converse API response with text and image content blocks."""
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "Here is the generated image."},
                    {
                        "image": {
                            "format": "png",
                            "source": {"bytes": b"\x89PNG\r\n\x1a\nfake-image-bytes"},
                        }
                    },
                ],
            }
        },
        "usage": {"inputTokens": 100, "outputTokens": 200},
        "metrics": {"latencyMs": 1500},
    }


@pytest.fixture
def mock_converse_text_only_response() -> dict:  # type: ignore[type-arg]
    """Converse API response with text only (no image)."""
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "I can help you with image generation. What would you like?"},
                ],
            }
        },
        "usage": {"inputTokens": 50, "outputTokens": 30},
        "metrics": {"latencyMs": 500},
    }
