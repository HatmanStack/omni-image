"""Tests for AWS client manager singleton."""

import threading
from unittest.mock import MagicMock, patch

from src.services.aws_client import AWSClientManager


class TestAWSClientManager:
    def setup_method(self) -> None:
        AWSClientManager._reset()

    def teardown_method(self) -> None:
        AWSClientManager._reset()

    def test_singleton_behavior(self) -> None:
        mgr1 = AWSClientManager()
        mgr2 = AWSClientManager()
        assert mgr1 is mgr2

    def test_reset_clears_singleton(self) -> None:
        mgr1 = AWSClientManager()
        AWSClientManager._reset()
        mgr2 = AWSClientManager()
        assert mgr1 is not mgr2

    @patch("boto3.client")
    def test_bedrock_client_creates_with_correct_region(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        mgr = AWSClientManager()
        client = mgr.bedrock_client

        assert client is mock_client
        mock_boto3.assert_called_once()
        call_kwargs = mock_boto3.call_args
        assert call_kwargs.kwargs["service_name"] == "bedrock-runtime"
        assert call_kwargs.kwargs["region_name"] == "us-west-2"

    @patch("boto3.client")
    def test_s3_client_creates_correctly(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        mgr = AWSClientManager()
        client = mgr.s3_client

        assert client is mock_client
        mock_boto3.assert_called_once()
        call_kwargs = mock_boto3.call_args
        assert call_kwargs.kwargs["service_name"] == "s3"

    @patch("boto3.client")
    def test_thread_safety_same_instance(self, mock_boto3: MagicMock) -> None:
        instances: list[AWSClientManager] = []

        def create_instance() -> None:
            instances.append(AWSClientManager())

        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(inst is instances[0] for inst in instances)
