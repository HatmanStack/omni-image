"""Tests for Bedrock Converse service."""

from unittest.mock import MagicMock, patch

import pytest

from src.models.schemas import ConverseResult
from src.utils.exceptions import BedrockError


class TestBedrockService:
    def setup_method(self) -> None:
        from src.services.aws_client import AWSClientManager

        AWSClientManager._reset()

    def teardown_method(self) -> None:
        from src.services.aws_client import AWSClientManager
        from src.services.bedrock_service import reset_bedrock_service

        reset_bedrock_service()
        AWSClientManager._reset()

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_converse_text_and_image(
        self,
        mock_aws_cls: MagicMock,
        mock_converse_response: dict,  # type: ignore[type-arg]
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = mock_converse_response
        mock_mgr.executor = None  # skip async storage

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        messages = [{"role": "user", "content": [{"text": "Generate an image"}]}]
        result = service.converse(messages)

        assert isinstance(result, ConverseResult)
        assert result.text == "Here is the generated image."
        assert result.image_bytes is not None
        assert result.image_format == "png"
        assert result.usage == {"inputTokens": 100, "outputTokens": 200}
        assert result.latency_ms == 1500

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_converse_text_only(
        self,
        mock_aws_cls: MagicMock,
        mock_converse_text_only_response: dict,  # type: ignore[type-arg]
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = mock_converse_text_only_response
        mock_mgr.executor = None

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        result = service.converse(messages)

        assert result.text is not None
        assert result.image_bytes is None

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_converse_image_only(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "image": {
                                "format": "png",
                                "source": {"bytes": b"\x89PNGimage-only"},
                            }
                        },
                    ],
                }
            },
            "usage": {"inputTokens": 10, "outputTokens": 5},
            "metrics": {"latencyMs": 800},
        }
        mock_mgr.bedrock_client.converse.return_value = response
        mock_mgr.executor = None

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        result = service.converse([{"role": "user", "content": [{"text": "draw"}]}])

        assert result.text is None
        assert result.image_bytes is not None

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_converse_raises_bedrock_error_on_client_error(self, mock_aws_cls: MagicMock) -> None:
        from botocore.exceptions import ClientError

        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Too many requests"}},
            "Converse",
        )

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        with pytest.raises(BedrockError, match="Too many requests"):
            service.converse([{"role": "user", "content": [{"text": "test"}]}])

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_converse_raises_bedrock_error_on_unexpected_response(
        self, mock_aws_cls: MagicMock
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = {"output": {}}
        mock_mgr.executor = None

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        with pytest.raises(BedrockError):
            service.converse([{"role": "user", "content": [{"text": "test"}]}])

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_store_response_async_submits_to_executor(
        self,
        mock_aws_cls: MagicMock,
        mock_converse_response: dict,  # type: ignore[type-arg]
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = mock_converse_response
        mock_executor = MagicMock()
        mock_mgr.executor = mock_executor

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        service.converse([{"role": "user", "content": [{"text": "test"}]}])

        mock_executor.submit.assert_called_once()

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_store_response_sync_stores_correct_keys(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        messages = [{"role": "user", "content": [{"text": "test"}]}]
        result = ConverseResult(
            text="response text",
            image_bytes=b"fake-image",
            usage={"inputTokens": 10},
            latency_ms=500,
        )

        service._store_response_sync(messages, result)

        calls = mock_mgr.s3_client.put_object.call_args_list
        assert len(calls) == 3  # request, image, response
        keys = [call.kwargs["Key"] for call in calls]
        assert any(k.startswith("requests/") for k in keys)
        assert any(k.startswith("images/") for k in keys)
        assert any(k.startswith("responses/") for k in keys)

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_s3_storage_failure_logged_not_raised(self, mock_aws_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.s3_client.put_object.side_effect = Exception("S3 down")

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        messages = [{"role": "user", "content": [{"text": "test"}]}]
        result = ConverseResult(text="ok", image_bytes=b"img")

        # Should not raise
        service._store_response_sync(messages, result)

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_inference_config_omitted_when_none(
        self,
        mock_aws_cls: MagicMock,
        mock_converse_text_only_response: dict,  # type: ignore[type-arg]
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = mock_converse_text_only_response
        mock_mgr.executor = None

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        service.converse(
            [{"role": "user", "content": [{"text": "test"}]}],
            inference_config=None,
        )

        call_kwargs = mock_mgr.bedrock_client.converse.call_args.kwargs
        assert "inferenceConfig" not in call_kwargs

    @patch("src.services.bedrock_service.AWSClientManager")
    def test_inference_config_passed_when_provided(
        self,
        mock_aws_cls: MagicMock,
        mock_converse_text_only_response: dict,  # type: ignore[type-arg]
    ) -> None:
        mock_mgr = MagicMock()
        mock_aws_cls.return_value = mock_mgr
        mock_mgr.bedrock_client.converse.return_value = mock_converse_text_only_response
        mock_mgr.executor = None

        from src.services.bedrock_service import BedrockService

        service = BedrockService()
        config = {"maxTokens": 1000, "temperature": 0.7}
        service.converse(
            [{"role": "user", "content": [{"text": "test"}]}],
            inference_config=config,
        )

        call_kwargs = mock_mgr.bedrock_client.converse.call_args.kwargs
        assert call_kwargs["inferenceConfig"] == config
